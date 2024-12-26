from typing import final

from collections.abc import Generator

from pydantic import BaseModel, ConfigDict, Field

from src.core.exceptions import TaskTypeNotFoundError
from src.protocols.task import TaskProtocol
from src.schemas.enums import TaskType
from src.schemas.task import FileTaskConfig, HttpTaskConfig, TaskConfig
from src.task.base import BaseTask
from src.task.file import FileTask
from src.task.http import HttpTask


class TaskImplementation(BaseModel):
    """Model for mapping task type to its implementation and configuration"""

    task_class: type[TaskProtocol]
    config_class: type[TaskConfig]

    model_config = ConfigDict(arbitrary_types_allowed=True)


@final
class TaskRegistry(BaseModel):
    """Task registry with factory method"""

    task_types: dict[TaskType, TaskImplementation] = Field(
        default_factory=lambda: {
            TaskType.HTTP: TaskImplementation(task_class=HttpTask, config_class=HttpTaskConfig),
            TaskType.FILE: TaskImplementation(task_class=FileTask, config_class=FileTaskConfig),
        }
    )

    def create_task(self, config: TaskConfig) -> Generator[BaseTask, None, None]:
        """
        Create task instance based on configuration.

        Args:
            config: Task configuration

        Yields:
            Created task instance

        Raises:
            TaskTypeNotFoundError: If task type is not registered
        """
        task_type_config = self.task_types.get(config.task_type)
        if task_type_config is None:
            raise TaskTypeNotFoundError(f"Task type {config.task_type} is not registered")
        yield task_type_config.task_class(config)  # type: ignore  # noqa: PGH003
