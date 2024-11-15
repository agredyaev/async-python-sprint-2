class BaseError(Exception): ...


class StateError(BaseError):
    """Base error for state operations."""
    ...


class StateFileError(StateError):
    """Error related to state file operations."""
    ...


class StateValidationError(StateError):
    """Error related to state validation."""
    ...


class ContextError(BaseError):
    """Base error for context operations."""
    ...


class ContextNotFoundError(ContextError):
    """Error raised when context is not found."""
    ...


class ContextValidationError(ContextError):
    """Error raised when context validation fails."""
    ...


class ContextVersionError(ContextError):
    """Error raised when context version conflict occurs."""
    ...


class SchedulerError(BaseError):
    """Base exception for scheduler errors."""
    ...

class TaskPoolError(BaseError):
    """Base exception for task pool errors."""
    ...

class BaseTaskError(BaseError):
    """Base exception for task errors."""
    ...

class TaskError(BaseTaskError):
    """Base exception for task errors."""
    ...


class TaskCreationError(TaskError):
    """Error raised when task creation fails."""
    ...


class TaskTypeNotFoundError(TaskError):
    """Error raised when task type is not registered."""
    ...


class TaskConfigValidationError(TaskError):
    """Error raised when task configuration is invalid."""
    ...