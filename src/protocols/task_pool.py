from typing import Protocol, runtime_checkable

from collections.abc import Generator
from datetime import datetime
from uuid import UUID

from src.schemas import Context, TaskConfig, TaskMetrics, TaskState


@runtime_checkable
class TaskProtocol(Protocol):
    """Protocol defining the interface for all task types."""

    @property
    def task_id(self) -> UUID:
        """Returns unique task identifier."""
        ...

    @property
    def priority(self) -> int:
        """Returns task priority."""
        ...

    @property
    def dependencies(self) -> list[UUID]:
        """Returns list of dependent task IDs."""
        ...

    @property
    def metrics(self) -> TaskMetrics:
        """Returns task execution metrics."""
        ...

    def execute(self, context: Context) -> Generator[None, None, None]:
        """
        Executes the task with given context.

        Args:
            context: Task execution context

        Returns:
            Generator yielding None on each execution step
        """
        ...

    def get_state(self) -> TaskState:
        """Returns current task state."""
        ...

    def set_state(self, state: TaskState) -> None:
        """Updates task state."""
        ...


@runtime_checkable
class TaskFactoryProtocol(Protocol):
    """Protocol for task factory implementation."""

    def create_task(self, config: TaskConfig) -> Generator[None, None, TaskProtocol]:
        """
        Creates task instance based on configuration.

        Args:
            config: Task configuration

        Returns:
            Generator yielding created task instance
        """
        ...


@runtime_checkable
class ContextManagerProtocol(Protocol):
    """Protocol for context management operations."""

    def create_context(self, pipeline_id: UUID | None = None) -> Generator[None, None, Context]:
        """
        Creates new execution context.

        Args:
            pipeline_id: Optional pipeline identifier

        Returns:
            Generator yielding created context
        """
        ...

    def get_context(self, task_id: UUID) -> Generator[None, None, Context]:
        """
        Retrieves context by task ID.

        Args:
            task_id: Task identifier

        Returns:
            Generator yielding task context
        """
        ...

    def update_context(self, context: Context) -> Generator[None, None, None]:
        """
        Updates existing context.

        Args:
            context: Context to update

        Returns:
            Generator yielding None on each update step
        """
        ...

    def cleanup_context(self, pipeline_id: UUID) -> Generator[None, None, None]:
        """
        Removes context by pipeline ID.

        Args:
            pipeline_id: Pipeline identifier

        Returns:
            Generator yielding None on each cleanup step
        """
        ...

    def merge_contexts(self, source: Context, target: Context) -> Generator[None, None, Context]:
        """
        Merges source context into target context.

        Args:
            source: Source context
            target: Target context

        Returns:
            Generator yielding merged context
        """
        ...

    def associate_task(self, task_id: UUID, context_id: UUID) -> Generator[None, None, None]:
        """
        Associates task with context.

        Args:
            task_id: Task identifier
            context_id: Context identifier

        Returns:
            Generator yielding None on completion
        """
        ...


@runtime_checkable
class StateManagerProtocol(Protocol):
    """Protocol for managing scheduler and task states."""

    def save_state(self) -> Generator[None, None, None]:
        """
        Persists current state to storage.

        Returns:
            Generator yielding None on each save step
        """
        ...

    def load_state(self) -> Generator[None, None, None]:
        """
        Loads state from storage.

        Returns:
            Generator yielding None on each load step
        """
        ...

    def update_task_state(self, task_id: UUID, state: TaskState) -> Generator[None, None, None]:
        """
        Updates task state.

        Args:
            task_id: Task identifier
            state: New task state

        Returns:
            Generator yielding None on completion
        """
        ...

    def get_task_state(self, task_id: UUID) -> Generator[None, None, TaskState]:
        """
        Retrieves task state.

        Args:
            task_id: Task identifier

        Returns:
            Generator yielding task state
        """
        ...

    def cleanup_states(self, older_than: datetime) -> Generator[None, None, None]:
        """
        Removes old state records.

        Args:
            older_than: Timestamp for cleanup

        Returns:
            Generator yielding None on each cleanup step
        """
        ...


@runtime_checkable
class TaskPoolProtocol(Protocol):
    """Protocol for task pool management."""

    def add_task(self, task: TaskProtocol) -> Generator[None, None, None]:
        """
        Adds task to the pool.

        Args:
            task: Task to add

        Returns:
            Generator yielding None on completion
        """
        ...

    def get_next_task(self) -> Generator[None, None, TaskProtocol | None]:
        """
        Returns next task for execution.

        Returns:
            Generator yielding next task or None
        """
        ...

    def remove_task(self, task_id: UUID) -> Generator[None, None, None]:
        """
        Removes task from pool.

        Args:
            task_id: Task identifier

        Returns:
            Generator yielding None on completion
        """
        ...

    def get_running_tasks(self) -> Generator[None, None, list[TaskProtocol]]:
        """
        Returns list of currently running tasks.

        Returns:
            Generator yielding list of running tasks
        """
        ...

    def get_pending_tasks(self) -> Generator[None, None, list[TaskProtocol]]:
        """
        Returns list of pending tasks.

        Returns:
            Generator yielding list of pending tasks
        """
        ...
