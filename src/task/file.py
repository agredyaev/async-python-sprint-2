from collections.abc import Callable, Generator
from pathlib import Path

from src.core.exceptions import TaskError
from src.schemas import Context, FileOperation, FileTaskConfig
from src.task.base import BaseTask

type PathStr = str
type OperationFunc = Callable[[PathStr, Context], Generator[None, None, None]]


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
        self._operations: dict[FileOperation, OperationFunc] = {
            FileOperation.READ: self._read_file,
            FileOperation.WRITE: self._write_file,
            FileOperation.APPEND: self._append_file,
            FileOperation.DELETE: self._delete_file,
            FileOperation.CREATE: self._create_file,
        }

    def _do_execute(self, context: Context) -> Generator[None, None, None]:
        """
        Execute file operation based on configuration.

        Args:
            context: Task execution context
        """
        operation = self._config.operation
        path = self._config.file_path

        try:
            operation_func = self._operations.get(operation)
            if operation_func:
                yield from operation_func(path, context)

            context.data["file_path"] = path
            context.data["operation"] = operation.value

        except TaskError as e:
            context.data["error"] = str(e)
            raise

    def _read_file(self, path: PathStr, context: Context) -> Generator[None, None, None]:
        with Path(path).open() as f:
            content = f.read()
            yield
            context.results[str(self.task_id)] = content

    def _write_file(self, path: PathStr) -> Generator[None, None, None]:
        yield
        with Path(path).open("w") as f:
            f.write(self._config.content or "")
            yield

    def _append_file(self, path: PathStr) -> Generator[None, None, None]:
        yield
        with Path(path).open("a") as f:
            f.write(self._config.content or "")
            yield

    @staticmethod
    def _delete_file(path: PathStr) -> Generator[None, None, None]:
        if Path(path).exists():
            yield
            Path(path).unlink()
            yield

    def _create_file(self, path: PathStr) -> Generator[None, None, None]:
        if not Path(path).exists():
            yield
            with Path(path).open("w") as f:
                if self._config.content:
                    f.write(self._config.content)
                yield
