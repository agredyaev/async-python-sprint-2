from typing import Protocol, runtime_checkable

from collections.abc import Generator

from src.protocols.task import TaskProtocol
from src.schemas import TaskConfig


@runtime_checkable
class TaskFactoryProtocol(Protocol):
    """Protocol for task factory implementation."""

    def create_task(self, config: TaskConfig) -> Generator[TaskProtocol, None, None]:
        """
        Creates task instance based on configuration.

        Args:
            config: Task configuration

        Returns:
            Generator yielding created task instance
        """
        ...
