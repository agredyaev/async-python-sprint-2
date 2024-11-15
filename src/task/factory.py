from typing import final

from collections.abc import Mapping
from threading import RLock

from pydantic import BaseModel, ValidationError

from src.core.exceptions import TaskConfigValidationError, TaskCreationError, TaskTypeNotFoundError
from src.protocols import TaskFactoryProtocol, TaskProtocol
from src.schemas import FileTaskConfig, HttpTaskConfig, TaskConfig, TaskType
from src.task.file import FileTask
from src.task.http import HttpTask


class TaskTypeConfig(BaseModel):
    task_class: type[TaskProtocol]
    config_class: type[TaskConfig]

@final
class TaskFactory(TaskFactoryProtocol):
    """Factory for creating task instances based on configuration."""

    def __init__(self) -> None:
        """Initialize task factory with default task types."""
        self._task_types: dict[TaskType, TaskTypeConfig] = {}
        self._lock = RLock()
        self._register_default_tasks()

    def _register_default_tasks(self) -> None:
        """Register default task implementations."""
        self.register_task_type(TaskType.FILE, FileTask, FileTaskConfig)
        self.register_task_type(TaskType.HTTP, HttpTask, HttpTaskConfig)

    def register_task_type(self, task_type: TaskType, task_class: type[TaskProtocol], config_class: type[TaskConfig]) -> None:
        """
        Register new task type with its implementation class.

        Args:
            task_type: Type of the task
            task_class: Task implementation class
            config_class: Configuration class for the task

        Raises:
            ValueError: If task_type, task_class or config_class is invalid
        """
        if not isinstance(task_type, TaskType):
            raise ValueError(f"Task type must be instance of TaskType enum, got {type(task_type)}")

        if not isinstance(task_class, type) or not issubclass(task_class, TaskProtocol):
            raise ValueError(f"Task class must be a subclass of TaskProtocol, got {task_class}")

        if not isinstance(config_class, type) or not issubclass(config_class, TaskConfig):
            raise ValueError(f"Config class must be a subclass of TaskConfig, got {config_class}")

        with self._lock:
            self._task_types[task_type] = TaskTypeConfig(task_class=task_class, config_class=config_class)

    def create_task(self, config: TaskConfig) -> TaskProtocol:
        """
        Create task instance based on configuration.

        Args:
            config: Task configuration

        Returns:
            Created task instance

        Raises:
            TaskCreationError: If task creation fails
        """
        try:
            return self._create_task_internal(config)
        except (TaskTypeNotFoundError, TaskConfigValidationError, ValidationError) as e:
            raise TaskCreationError(f"Failed to create task: {e!s}") from e

    def _create_task_internal(self, config: TaskConfig) -> TaskProtocol:
        """
        Internal method for task creation with proper type checking.

        Args:
            config: Task configuration

        Returns:
            Created task instance

        Raises:
            TaskTypeNotFoundError: If task type is not registered
            TaskConfigValidationError: If configuration is invalid
        """
        if not isinstance(config.task_type, TaskType):
            raise TaskConfigValidationError(f"Invalid task type: {config.task_type}. Must be instance of TaskType enum.")

        with self._lock:
            task_type_config = self._task_types.get(config.task_type)

        if task_type_config is None:
            raise TaskTypeNotFoundError(f"Task type {config.task_type} is not registered")

        if not isinstance(config, task_type_config.config_class):
            raise TaskConfigValidationError(
                f"Invalid configuration type for {config.task_type}. "
                f"Expected {task_type_config.config_class.__name__}, got {type(config).__name__}"
            )

        return task_type_config.task_class(config)

    def unregister_task_type(self, task_type: TaskType) -> None:
        """
        Remove task type registration.

        Args:
            task_type: Type of task to unregister

        Raises:
            ValueError: If task_type is not valid
        """
        if not isinstance(task_type, TaskType):
            raise ValueError(f"Task type must be instance of TaskType enum, got {type(task_type)}")

        with self._lock:
            self._task_types.pop(task_type, None)

    def get_registered_types(self) -> list[TaskType]:
        """
        Get list of registered task types.

        Returns:
            List of registered task types
        """
        with self._lock:
            return list(self._task_types.keys())

    def get_task_config(self) -> Mapping[TaskType, type[TaskConfig]]:
        """
        Get mapping of task types to their configuration classes.

        Returns:
            Mapping of task types to configuration classes
        """
        with self._lock:
            return {task_type: config.config_class for task_type, config in self._task_types.items()}
