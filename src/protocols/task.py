from typing import Protocol, runtime_checkable

from collections.abc import Generator

from src.schemas import Context, TaskState


@runtime_checkable
class TaskProtocol(Protocol):
    """Protocol defining the interface for all task types."""

    def execute(self, context: Context) -> Generator[None, None, None]:
        """
        Executes the task with given context.

        Args:
            context: Task execution context

        Returns:
            Generator yielding None on each execution step
        """
        ...

    def set_state(self, state: TaskState) -> None:
        """Updates task state."""
        ...
