from enum import IntEnum, StrEnum, auto


class TaskState(StrEnum):
    """Available states for task execution lifecycle."""

    CREATED = auto()
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    RETRY_PENDING = auto()


class TaskType(StrEnum):
    """Available task types in the system."""

    FILE = auto()
    HTTP = auto()


class TaskPriority(IntEnum):
    """Task execution priority levels."""

    LOW = 0
    MEDIUM = 5
    HIGH = 10
    CRITICAL = 20


class FileOperation(StrEnum):
    """Available file system operations."""

    CREATE = auto()
    READ = auto()
    WRITE = auto()
    DELETE = auto()
    APPEND = auto()


class MetricType(StrEnum):
    """Types of metrics collected during task execution."""

    EXECUTION_TIME = auto()
    RETRY_COUNT = auto()
    ERROR_COUNT = auto()
    MEMORY_USAGE = auto()
    TASK_COUNT = auto()
