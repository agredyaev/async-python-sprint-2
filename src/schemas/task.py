from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.helpers import get_current_timestamp
from src.schemas.enums import FileOperation, TaskPriority, TaskType
from src.schemas.mixins import CreatedAtMixin, UpdatedAtMixin, UUIDMixin


class TaskBase(BaseModel):
    model_config = ConfigDict(frozen=False, validate_assignment=True)


class TaskMetrics(TaskBase, CreatedAtMixin, UpdatedAtMixin):
    """Collection of metrics for task execution monitoring and analysis."""

    execution_time: float = Field(default=0.0, description="Execution time in seconds")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    error_count: int = Field(default=0, description="Number of errors occurred")
    memory_usage: float = Field(default=0.0, description="Memory usage in MB")
    last_error: str | None = Field(default=None, description="Last error message")


class TaskConfig(TaskBase, UUIDMixin):
    """Base configuration for task execution."""

    task_type: TaskType = Field(..., description="Type of the task")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task execution priority")
    dependencies: list[UUID] = Field(default_factory=list, description="List of dependent task IDs")
    timeout: float = Field(default=60.0, ge=0, description="Execution timeout in seconds")
    max_retries: int = Field(default=3, ge=0, description="Maximum number of retry attempts")
    start_time: datetime | None = Field(default=None, description="Scheduled start time")

    @model_validator(mode="after")
    def validate_start_time(self) -> "TaskConfig":
        """Validates that start_time is not in the past."""
        if self.start_time and self.start_time < get_current_timestamp():
            raise ValueError("Start time cannot be in the past")
        return self


class FileTaskConfig(TaskConfig):
    """Configuration for file system operation tasks."""

    task_type: TaskType = Field(TaskType.FILE, frozen=True)
    operation: FileOperation = Field(..., description="Type of file operation")
    file_path: str = Field(..., min_length=1, description="Target file path")
    content: str | None = Field(None, description="Content for write operations")

    @model_validator(mode="after")
    def validate_content_required(self) -> "FileTaskConfig":
        """Validates content presence for write operations."""
        if self.operation in [FileOperation.WRITE, FileOperation.APPEND] and self.content is None:
            raise ValueError("Content is required for write and append operations")
        return self


class HttpTaskConfig(TaskConfig):
    """Configuration for HTTP request tasks."""

    task_type: TaskType = Field(TaskType.HTTP, frozen=True)
    url: str = Field(..., description="Target URL for HTTP request")
    method: str = Field(default="GET", description="HTTP method")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    timeout: float = Field(default=30.0, ge=0, description="HTTP request timeout")
