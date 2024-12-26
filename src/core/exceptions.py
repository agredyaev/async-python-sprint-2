class BaseError(Exception):
    """Base exception class."""


class UnsupportedPythonVersionError(BaseError):
    """Error raised when unsupported python version is detected."""


class StateError(BaseError):
    """Base error for state operations."""


class StateLockError(StateError):
    """Lock operation failed"""


class StateLoadError(StateError):
    """State load operation failed"""


class StateSaveError(StateError):
    """State save operation failed"""


class StateNotFoundError(StateError):
    """State not found"""


class StateFileError(StateError):
    """Error related to state file operations."""


class StateValidationError(StateError):
    """Error related to state validation."""


class ContextError(BaseError):
    """Base error for context operations."""


class ContextNotFoundError(ContextError):
    """Error raised when context is not found."""


class ContextValidationError(ContextError):
    """Error raised when context validation fails."""


class ContextVersionError(ContextError):
    """Error raised when context version conflict occurs."""


class SchedulerError(BaseError):
    """Base exception for scheduler errors."""


class TaskPoolError(BaseError):
    """Base exception for task pool errors."""


class BaseTaskError(BaseError):
    """Base exception for task errors."""


class TaskError(BaseTaskError):
    """Base exception for task errors."""


class TaskCreationError(TaskError):
    """Error raised when task creation fails."""


class TaskMaxRetriesError(TaskError):
    """Error raised when task max retries is exceeded."""


class TaskTypeNotFoundError(TaskError):
    """Error raised when task type is not registered."""


class TaskConfigValidationError(TaskError):
    """Error raised when task configuration is invalid."""


class TaskExecutionError(TaskError):
    """Error raised when task execution fails."""
