import heapq

from collections import defaultdict
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from uuid import UUID

from pydantic import BaseModel, Field

from src.core.exceptions import TaskPoolError
from src.core.settings import settings
from src.protocols import TaskPoolProtocol, TaskProtocol
from src.schemas import TaskState


class ExecutionPriority(BaseModel):
    """Model for calculating task execution priority."""
    base_priority: int = Field(default=0, ge=0)
    wait_time_weight: float = Field(default=0.1, ge=0)
    retry_weight: float = Field(default=5, ge=0)

    def calculate_priority(self, wait_time: float, retry_count: int) -> float:
        """Calculate priority based on wait time and retry count."""
        return self.base_priority + (wait_time * self.wait_time_weight) + (retry_count * self.retry_weight)

@dataclass(order=True)
class PrioritizedTask:
    """Task wrapper with priority queue support."""
    priority: float
    added_time: datetime = field(compare=False)
    task: TaskProtocol = field(compare=False)
    execution_priority: ExecutionPriority = field(compare=False, default_factory=ExecutionPriority)

    def __post_init__(self) -> None:
        """Initialize with inverted priority for min-heap."""
        self.priority = -self.priority

    def recalculate_priority(self) -> None:
        """Recalculate task priority based on wait time and retries."""
        wait_time = (datetime.now() - self.added_time).total_seconds()
        retry_count = getattr(self.task.metrics, "retry_count", 0)
        self.priority = -self.execution_priority.calculate_priority(
            wait_time=wait_time,
            retry_count=retry_count
        )

class TaskPool(TaskPoolProtocol):
    """Implementation of task pool with priority-based scheduling."""

    def __init__(self) -> None:
        self._config = settings.scheduler
        self._lock = RLock()
        self._pending_tasks: list[PrioritizedTask] = []
        self._running_tasks: dict[UUID, TaskProtocol] = {}
        self._completed_tasks: dict[UUID, TaskProtocol] = {}
        self._failed_tasks: dict[UUID, TaskProtocol] = {}
        self._task_dependencies: defaultdict[UUID, set[UUID]] = defaultdict(set)
        self._dependent_tasks: defaultdict[UUID, set[UUID]] = defaultdict(set)
        self._task_added_times: dict[UUID, datetime] = {}
        self._task_priorities: dict[UUID, ExecutionPriority] = {}

    def add_task(self, task: TaskProtocol) -> Generator[None, None, None]:
        if not task:
            raise TaskPoolError("Task cannot be None")

        task_id = task.task_id
        with self._lock:
            yield from self._check_task_exists(task_id)

            if task.dependencies:
                self._task_dependencies[task_id].update(task.dependencies)
                for dep_id in task.dependencies:
                    self._dependent_tasks[dep_id].add(task_id)

            prioritized_task = PrioritizedTask(
                priority=task.priority,
                added_time=datetime.now(),
                task=task,
                execution_priority=ExecutionPriority()
            )

            heapq.heappush(self._pending_tasks, prioritized_task)
            self._task_added_times[task_id] = prioritized_task.added_time
            self._task_priorities[task_id] = prioritized_task.execution_priority
            task.set_state(TaskState.PENDING)

        yield

    def get_next_task(self) -> Generator[None, None, TaskProtocol | None]:
        with self._lock:
            if len(self._running_tasks) >= self._config.max_concurrent_tasks:
                yield
                return None

            available_tasks: list[PrioritizedTask] = []
            task_to_run = None

            while self._pending_tasks:
                prioritized_task = heapq.heappop(self._pending_tasks)
                prioritized_task.recalculate_priority()

                if (yield from self._can_execute_task(prioritized_task.task)):
                    task_to_run = prioritized_task.task
                    break
                else:
                    available_tasks.append(prioritized_task)

            for task in available_tasks:
                heapq.heappush(self._pending_tasks, task)

            if task_to_run:
                self._running_tasks[task_to_run.task_id] = task_to_run
                task_to_run.set_state(TaskState.RUNNING)

            yield
            return task_to_run

    def remove_task(self, task_id: UUID) -> Generator[None, None, None]:
        with self._lock:
            task = self._running_tasks.pop(task_id, None)
            if task:
                if task.get_state() == TaskState.COMPLETED:
                    self._completed_tasks[task_id] = task
                else:
                    self._failed_tasks[task_id] = task

                for dependent_id in self._dependent_tasks.pop(task_id, set()):
                    self._task_dependencies[dependent_id].discard(task_id)

                self._task_added_times.pop(task_id, None)
                self._task_priorities.pop(task_id, None)
                yield
                return

            raise TaskPoolError(f"Task {task_id} not found in running tasks")

    def get_running_tasks(self) -> Generator[None, None, list[TaskProtocol]]:
        with self._lock:
            yield
            return list(self._running_tasks.values())

    def get_pending_tasks(self) -> Generator[None, None, list[TaskProtocol]]:
        with self._lock:
            yield
            return [pt.task for pt in self._pending_tasks]

    def _check_task_exists(self, task_id: UUID) -> Generator[None, None, None]:
        if task_id in self._running_tasks or task_id in self._completed_tasks or \
                task_id in self._failed_tasks or task_id in self._task_added_times:
            raise TaskPoolError(f"Task {task_id} already exists in the pool")
        yield

    def _can_execute_task(self, task: TaskProtocol) -> Generator[None, None, bool]:
        task_deps = self._task_dependencies.get(task.task_id, set())
        if not task_deps:
            yield
            return True

        for dep_id in task_deps:
            if dep_id not in self._completed_tasks:
                yield
                return False

        yield
        return True

    def cleanup_completed(self, older_than: datetime) -> Generator[None, None, None]:
        with self._lock:
            for task_dict in (self._completed_tasks, self._failed_tasks):
                to_remove = [
                    task_id for task_id, task in task_dict.items()
                    if task.metrics.updated_at <= older_than
                ]
                for task_id in to_remove:
                    task_dict.pop(task_id)
                    yield

    def get_task_counts(self) -> dict[TaskState, int]:
        with self._lock:
            return {
                TaskState.PENDING: len(self._pending_tasks),
                TaskState.RUNNING: len(self._running_tasks),
                TaskState.COMPLETED: len(self._completed_tasks),
                TaskState.FAILED: len(self._failed_tasks)
            }

    def get_task_wait_time(self, task_id: UUID) -> float | None:
        added_time = self._task_added_times.get(task_id)
        if added_time:
            return (datetime.now() - added_time).total_seconds()
        return None
