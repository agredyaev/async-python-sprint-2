from abc import ABC, abstractmethod
from typing import Generator, Any
from uuid import UUID
from datetime import datetime
import os
import requests

from src.schemas import (
    TaskState,
    Context,
    TaskConfig,
    FileTaskConfig,
    HttpTaskConfig,
    TaskMetrics,
    FileOperation
)


class BaseTask(ABC):
    """Base implementation of task functionality."""

    def __init__(self, config: TaskConfig) -> None:
        """Initialize base task parameters."""
        self._config = config
        self._state = TaskState.CREATED
        self._metrics = TaskMetrics()
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
        self._error: Optional[Exception] = None
        
    @property
    def task_id(self) -> UUID:
        """Get task unique identifier."""
        return self._config.id
        
    @property
    def priority(self) -> int:
        """Get task priority."""
        return self._config.priority.value
        
    @property
    def dependencies(self) -> list[UUID]:
        """Get task dependencies."""
        return self._config.dependencies
        
    @property
    def metrics(self) -> TaskMetrics:
        """Get task execution metrics."""
        return self._metrics

    def get_state(self) -> TaskState:
        """Get current task state."""
        return self._state

    def set_state(self, state: TaskState) -> None:
        """Set new task state."""
        self._state = state

    def execute(self, context: Context) -> Generator[None, None, None]:
        """
        Execute task with provided context.
        
        Args:
            context: Task execution context
            
        Returns:
            Generator yielding None on each execution step
        """
        try:
            self._start_execution()
            yield
            
            yield from self._do_execute(context)
            yield
            
            self._complete_execution()
            yield
            
        except Exception as e:
            self._handle_error(e)
            raise

    @abstractmethod
    def _do_execute(self, context: Context) -> Generator[None, None, None]:
        """
        Implement actual task execution logic.
        
        Args:
            context: Task execution context
            
        Returns:
            Generator yielding None on each execution step
        """
        yield

    def _start_execution(self) -> None:
        """Prepare task for execution."""
        self._start_time = datetime.now()
        self._state = TaskState.RUNNING
        self._metrics.updated_at = datetime.now()

    def _complete_execution(self) -> None:
        """Handle successful task completion."""
        self._end_time = datetime.now()
        self._state = TaskState.COMPLETED
        if self._start_time:
            self._metrics.execution_time = (datetime.now() - self._start_time).total_seconds()
        self._metrics.updated_at = datetime.now()

    def _handle_error(self, error: Exception) -> None:
        """Handle task execution error."""
        self._error = error
        self._end_time = datetime.now()
        self._state = TaskState.FAILED
        self._metrics.error_count += 1
        self._metrics.last_error = str(error)
        self._metrics.updated_at = datetime.now()


class FileTask(BaseTask):
    """Implementation of file system operations task."""

    def __init__(self, config: FileTaskConfig) -> None:
        """
        Initialize file task.
        
        Args:
            config: File task configuration
        """
        super().__init__(config)
        self._config: FileTaskConfig = config

    def _do_execute(self, context: Context) -> Generator[None, None, None]:
        """
        Execute file operation based on configuration.
        
        Args:
            context: Task execution context
        """
        operation = self._config.operation
        path = self._config.file_path
        
        try:
            if operation == FileOperation.READ:
                with open(path, 'r') as f:
                    content = f.read()
                    yield  # After read operation
                    context.results[str(self.task_id)] = content
                    
            elif operation == FileOperation.WRITE:
                # Yield before write to allow interruption
                yield
                with open(path, 'w') as f:
                    f.write(self._config.content or '')
                    yield  # After write operation
                    
            elif operation == FileOperation.APPEND:
                # Yield before append to allow interruption
                yield
                with open(path, 'a') as f:
                    f.write(self._config.content or '')
                    yield  # After append operation
                    
            elif operation == FileOperation.DELETE:
                if os.path.exists(path):
                    # Yield before delete to allow interruption
                    yield
                    os.remove(path)
                    yield  # After delete operation
                    
            elif operation == FileOperation.CREATE:
                if not os.path.exists(path):
                    # Yield before create to allow interruption
                    yield
                    with open(path, 'w') as f:
                        if self._config.content:
                            f.write(self._config.content)
                    yield  # After create operation
            
            context.data['file_path'] = path
            context.data['operation'] = operation.value
            
        except Exception as e:
            context.data['error'] = str(e)
            raise


class HttpTask(BaseTask):
    """Implementation of HTTP request task."""

    def __init__(self, config: HttpTaskConfig) -> None:
        """
        Initialize HTTP task.
        
        Args:
            config: HTTP task configuration
        """
        super().__init__(config)
        self._config: HttpTaskConfig = config

    def _do_execute(self, context: Context) -> Generator[None, None, None]:
        """
        Execute HTTP request based on configuration.
        
        Args:
            context: Task execution context
        """
        try:
            # Yield before request to allow interruption
            yield
            
            # Create session
            session = requests.Session()
            yield
            
            # Prepare request
            response = session.request(
                method=self._config.method,
                url=self._config.url,
                headers=self._config.headers,
                timeout=self._config.timeout
            )
            yield  # After request
            
            # Process response
            response.raise_for_status()
            yield
            
            # Store results
            context.results[str(self.task_id)] = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text
            }
            
            context.data['url'] = self._config.url
            context.data['method'] = self._config.method
            
        except requests.RequestException as e:
            context.data['error'] = str(e)
            raise
        finally:
            session.close()
            yield
