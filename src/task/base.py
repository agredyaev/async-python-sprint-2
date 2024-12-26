from typing import ClassVar

from abc import ABC, abstractmethod
from collections.abc import Generator
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.core.exceptions import BaseTaskError, TaskMaxRetriesError
from src.helpers import get_current_timestamp
from src.protocols.task import TaskProtocol
from src.schemas.contex import Context
from src.schemas.enums import TaskState
from src.schemas.task import TaskConfig, TaskMetrics


class TaskError(BaseModel):
    message: str
    timestamp: datetime


class BaseTask(ABC, TaskProtocol):
    """Base implementation of task functionality."""

    DEFAULT_STATE: ClassVar[TaskState] = TaskState.CREATED

    def __init__(self, config: TaskConfig) -> None:
        """Initialize base task parameters."""
        self._config: TaskConfig = config
        self._state: TaskState = self.DEFAULT_STATE
        self._metrics: TaskMetrics = TaskMetrics()
        self._start_time: datetime | None = None
        self._end_time: datetime | None = None
        self._error: TaskError | None = None
        self._retry_count: int = 0

    @property
    def task_id(self) -> UUID:
        """Get task unique identifier."""
        return self._config.id

    @property
    def priority(self) -> int:
        """Get task priority."""
        return self._config.priority.value

    @property
    def dependencies(self) -> list[UUID]:
        """Get task dependencies."""
        return self._config.dependencies

    @property
    def metrics(self) -> TaskMetrics:
        """Get task execution metrics."""
        return self._metrics

    @property
    def config(self) -> TaskConfig:
        """Get task configuration."""
        return self._config

    @property
    def state(self) -> TaskState:
        """Get current task state."""
        return self._state

    def set_state(self, state: TaskState) -> None:
        """Set new task state."""
        self._state = state

    def execute(self, context: Context) -> Generator[None, None, None]:
        """
        Execute task with provided context.

        Args:
            context: Task execution context

        Returns:
            Generator yielding None on each execution step
        """
        while True:
            try:
                self._start_execution()
                yield from self._do_execute(context)
                self._complete_execution()
                break
            except BaseTaskError as e:
                if self._retry_count < self._config.max_retries:
                    self._retry_count += 1
                    self._state = TaskState.RETRY_PENDING
                    self._metrics.retry_count = self._retry_count
                    continue
                else:
                    self._handle_error(e)
                    raise TaskMaxRetriesError("Task max retries exceeded") from None
        yield None

    @abstractmethod
    def _do_execute(self, context: Context) -> Generator[None, None, None]:
        """
        Implement actual task execution logic.

        Args:
            context: Task execution context

        Returns:
            Generator yielding None on each execution step
        """
        yield

    def _start_execution(self) -> None:
        """Prepare task for execution."""
        self._start_time = get_current_timestamp()
        self._state = TaskState.RUNNING
        self._update_metrics()
        self._error = None

    def _complete_execution(self) -> None:
        """Handle successful task completion."""
        self._end_time = get_current_timestamp()
        self._state = TaskState.COMPLETED
        self._update_metrics()

    def _handle_error(self, error: Exception) -> None:
        """Handle task execution error."""
        self._error = TaskError(message=str(error), timestamp=get_current_timestamp())
        self._end_time = get_current_timestamp()
        self._state = TaskState.FAILED
        self._metrics.error_count += 1
        self._metrics.last_error = str(error)
        self._update_metrics()

    def _update_metrics(self) -> None:
        """Update task metrics."""
        self._metrics.updated_at = get_current_timestamp()
        if self._start_time:
            self._metrics.execution_time = (get_current_timestamp() - self._start_time).total_seconds()
