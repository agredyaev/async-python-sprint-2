from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, model_validator, computed_field


class TaskState(str, Enum):
    """Available states for task execution lifecycle."""
    CREATED = "created"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY_PENDING = "retry_pending"


class TaskType(str, Enum):
    """Available task types in the system."""
    FILE = "file"
    HTTP = "http"
    PROCESSING = "processing"


class TaskPriority(int, Enum):
    """Task execution priority levels."""
    LOW = 0
    MEDIUM = 5
    HIGH = 10
    CRITICAL = 20


class FileOperation(str, Enum):
    """Available file system operations."""
    CREATE = "create"
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    APPEND = "append"


class MetricType(str, Enum):
    """Types of metrics collected during task execution."""
    EXECUTION_TIME = "execution_time"
    RETRY_COUNT = "retry_count"
    ERROR_COUNT = "error_count"
    MEMORY_USAGE = "memory_usage"
    TASK_COUNT = "task_count"


class TaskMetrics(BaseModel):
    """Collection of metrics for task execution monitoring and analysis."""
    execution_time: float = Field(default=0.0, description="Execution time in seconds")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    error_count: int = Field(default=0, description="Number of errors occurred")
    memory_usage: float = Field(default=0.0, description="Memory usage in MB")
    last_error: Optional[str] = Field(default=None, description="Last error message")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = {
        "frozen": False,
        "validate_assignment": True
    }


class TaskConfig(BaseModel):
    """Base configuration for task execution."""
    task_id: UUID = Field(default_factory=uuid4, description="Unique task identifier")
    task_type: TaskType = Field(..., description="Type of the task")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task execution priority")
    dependencies: List[UUID] = Field(default_factory=list, description="List of dependent task IDs")
    timeout: float = Field(default=60.0, ge=0, description="Execution timeout in seconds")
    max_retries: int = Field(default=0, ge=0, description="Maximum number of retry attempts")
    start_time: Optional[datetime] = Field(default=None, description="Scheduled start time")
    task_specific_config: Dict[str, Any] = Field(default_factory=dict, description="Task-specific configuration")

    model_config = {
        "frozen": False,
        "validate_assignment": True
    }

    @model_validator(mode="after")
    def validate_start_time(self) -> "TaskConfig":
        """Validates that start_time is not in the past."""
        if self.start_time and self.start_time < datetime.now():
            raise ValueError("Start time cannot be in the past")
        return self


class FileTaskConfig(TaskConfig):
    """Configuration for file system operation tasks."""
    task_type: TaskType = Field(TaskType.FILE, frozen=True)
    operation: FileOperation = Field(..., description="Type of file operation")
    file_path: str = Field(..., min_length=1, description="Target file path")
    content: Optional[str] = Field(None, description="Content for write operations")

    @model_validator(mode="after")
    def validate_content_required(self):
        """Validates content presence for write operations."""
        if self.operation in [FileOperation.WRITE, FileOperation.APPEND] and self.content is None:
            raise ValueError("Content is required for write and append operations")
        return self


class HttpTaskConfig(TaskConfig):
    """Configuration for HTTP request tasks."""
    task_type: TaskType = Field(TaskType.HTTP, frozen=True)
    url: str = Field(..., description="Target URL for HTTP request")
    method: str = Field(default="GET", description="HTTP method")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    timeout: float = Field(default=30.0, ge=0, description="HTTP request timeout")


class ProcessingTaskConfig(TaskConfig):
    """Configuration for data processing tasks."""
    task_type: TaskType = Field(TaskType.PROCESSING, frozen=True)
    processor_type: str = Field(..., description="Type of data processor")
    input_data: Any = Field(..., description="Input data for processing")
    processing_params: Dict[str, Any] = Field(default_factory=dict, description="Processing parameters")


class Context(BaseModel):
    """Task execution context containing runtime data and results."""
    context_id: UUID = Field(default_factory=uuid4, description="Unique context identifier")
    pipeline_id: Optional[UUID] = Field(None, description="Pipeline identifier if task is part of pipeline")
    data: Dict[str, Any] = Field(default_factory=dict, description="Context data")
    results: Dict[str, Any] = Field(default_factory=dict, description="Execution results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Context metadata")
    version: int = Field(default=1, ge=1, description="Context version number")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = {
        "frozen": False,
        "validate_assignment": True
    }

    def update_version(self) -> None:
        """Updates context version and timestamp."""
        self.version += 1
        self.updated_at = datetime.now()


class PipelineConfig(BaseModel):
    """Configuration for task pipeline execution."""
    pipeline_id: UUID = Field(default_factory=uuid4, description="Unique pipeline identifier")
    tasks: List[TaskConfig] = Field(..., min_length=1, description="List of pipeline tasks")
    max_parallel: int = Field(default=1, ge=1, description="Maximum parallel tasks")
    timeout: float = Field(default=3600.0, ge=0, description="Pipeline timeout in seconds")

    model_config = {
        "frozen": False,
        "validate_assignment": True
    }

    @computed_field
    def task_count(self) -> int:
        """Returns the total number of tasks in pipeline."""
        return len(self.tasks)

    @model_validator(mode="after")
    def validate_tasks(self):
        """Validates task list is not empty."""
        if not self.tasks:
            raise ValueError("Pipeline must contain at least one task")
        return self


class SchedulerConfig(BaseModel):
    """Global scheduler configuration parameters."""
    max_concurrent_tasks: int = Field(default=10, ge=1, description="Maximum concurrent tasks")
    default_task_timeout: float = Field(default=60.0, ge=0, description="Default task timeout in seconds")
    state_check_interval: float = Field(default=1.0, ge=0.1, description="State check interval in seconds")
    cleanup_interval: float = Field(default=3600.0, ge=0, description="Cleanup interval in seconds")
    state_file_path: str = Field(default="scheduler_state.json", description="State file location")

    model_config = {
        "frozen": True,
        "validate_assignment": True
    }