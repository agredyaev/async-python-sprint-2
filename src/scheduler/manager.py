from types import TracebackType

from collections import deque
from collections.abc import Generator
from threading import RLock
from uuid import UUID

from src.core.logger import get_logger
from src.core.settings import settings
from src.helpers import get_current_timestamp
from src.protocols import ContextManagerProtocol, StateManagerProtocol
from src.schemas import TaskState
from src.task import BaseTask

logger = get_logger("scheduler")


class Scheduler:
    """Task scheduler."""

    def __init__(self, context_manager: ContextManagerProtocol, state_manager: StateManagerProtocol) -> None:
        self._context_manager = context_manager
        self._state_manager = state_manager
        self._config = settings.scheduler
        self._lock = RLock()
        self._tasks: deque[BaseTask] = deque(maxlen=self._config.max_concurrent_tasks)
        self._completed_tasks: set[UUID] = set()
        self._failed_tasks: set[UUID] = set()

    def add_task(self, task: BaseTask) -> None:
        """Add task to the scheduler queue."""
        self._tasks.append(task)
        context = next(self._context_manager.create_context())
        next(self._context_manager.associate_task(task.task_id, context.id))

    def _can_execute(self, task: BaseTask) -> bool:
        """Checks if all dependencies are completed and if start time is in the future."""
        for dependency in task.dependencies:
            if dependency in self._failed_tasks:
                task.set_state(TaskState.FAILED)
                self._failed_tasks.add(task.task_id)
                return False
            if dependency not in self._completed_tasks:
                return False
        return not (task.config.start_time and task.config.start_time > get_current_timestamp())

    def _process_task(self, task: BaseTask) -> Generator[None, None, None]:
        """Process task execution. Moves task to completed or failed states."""
        context = self._context_manager.get_context(task.task_id)
        yield from task.execute(context)
        match task.state:
            case TaskState.COMPLETED:
                self._completed_tasks.add(task.task_id)
            case TaskState.FAILED:
                self._failed_tasks.add(task.task_id)

    def run(self) -> Generator[None, None, None]:
        """Run event loop."""
        while self._tasks:
            task = self._tasks.popleft()
            if self._can_execute(task):
                yield from self._process_task(task)
            elif task.state != TaskState.FAILED:
                self._tasks.append(task)

    def __enter__(self) -> "Scheduler":
        """Logic when the scheduler starts."""
        logger.info("Starting scheduler.")
        with self._lock:
            next(self._state_manager.load())
        logger.info("Loaded state from storage.")
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        """Logic when the scheduler exits."""
        with self._lock:
            next(self._state_manager.save())
        logger.info("Saved state to storage.")
        logger.info("Scheduler stopped")
        if exc_val:
            logger.exception("Error occurred:%s, %s, %s", exc_type, exc_val, exc_tb)
