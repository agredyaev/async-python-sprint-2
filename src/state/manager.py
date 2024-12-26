from types import TracebackType

import fcntl
import os

from collections.abc import Generator
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from threading import RLock
from uuid import UUID

from src.core.exceptions import StateLoadError, StateLockError, StateNotFoundError, StateSaveError
from src.core.logger import get_logger
from src.core.settings import settings
from src.helpers import get_current_timestamp
from src.protocols import StateManagerProtocol
from src.schemas import StateData, TaskState, TaskStateData, TaskStates

logger = get_logger(__name__)


class FileStateManager(StateManagerProtocol):
    """File-based state manager with thread safety."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._states: TaskStates = TaskStates()
        self._dirty: set[UUID] = set()
        self._last_save: datetime | None = None

        self._state_file = Path(settings.state.file_path)
        self._lock_file = self._state_file.with_suffix(".lock")
        self._state_file.parent.mkdir(exist_ok=True)

        self._get_state = lru_cache(settings.state.cache_size)(self._get_cached_state)
        self._load_initial_state()

    def __enter__(self) -> "FileStateManager":
        """Context manager entry"""
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        """Context manager exit with guaranteed save"""
        if self._dirty:
            for _ in self.save():
                continue

    @staticmethod
    def _validate_version(version: int) -> None:
        """Validate state file version"""
        if version != settings.state.version:
            raise StateLoadError(f"Version mismatch: {version}")

    def _get_cached_state(self, task_id: UUID) -> TaskStateData | None:
        """Get state from cache"""
        return self._states.items.get(task_id)

    def _load_initial_state(self) -> None:
        """Load initial state on startup"""
        try:
            for _ in self.load():
                continue
        except Exception as e:
            logger.exception("Failed to load initial state", exc_info=e)

    @staticmethod
    def _acquire_lock(file_path: Path) -> int:
        """Acquire file lock"""
        try:
            fd = os.open(str(file_path), os.O_RDWR | os.O_CREAT)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            logger.exception("Failed to acquire lock")
            raise StateLockError("Unable to acquire lock") from e
        else:
            return fd

    @staticmethod
    def _release_lock(fd: int) -> None:
        """Release file lock"""
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        except OSError as e:
            logger.exception("Failed to release lock")
            raise StateLockError("Unable to release lock") from e

    def _write_state_file(self, data: StateData) -> None:
        """Write state file atomically"""
        temp_file = self._state_file.with_suffix(".tmp")
        try:
            temp_file.write_text(data.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
            temp_file.replace(self._state_file)
        except Exception as e:
            logger.exception("Failed to write state file")
            raise StateSaveError("Unable to write state file") from e
        finally:
            temp_file.unlink(missing_ok=True)

    def load(self) -> Generator[None, None, None]:
        """Load states from file"""
        if not self._state_file.exists():
            yield
            return

        fd = None
        try:
            fd = self._acquire_lock(self._lock_file)
            data = StateData.model_validate_json(self._state_file.read_text(encoding="utf-8"))
            self._validate_version(data.version)
            yield

            with self._lock:
                self._states = data.states
                self._dirty.clear()
                self._get_state.cache_clear()

        except Exception as e:
            logger.exception("State load failed")
            raise StateLoadError("Failed to load state") from e
        finally:
            if fd is not None:
                self._release_lock(fd)

    def save(self) -> Generator[None, None, None]:
        """Save states to file if modified"""
        if not self._dirty:
            yield
            return

        fd = None
        try:
            data = StateData(version=settings.state.version, updated=get_current_timestamp(), states=self._states)
            fd = self._acquire_lock(self._lock_file)
            self._write_state_file(data)
            yield

            with self._lock:
                self._dirty.clear()
                self._last_save = data.updated

        except Exception as e:
            logger.exception("State save failed")
            raise StateSaveError("Failed to save state") from e
        finally:
            if fd is not None:
                self._release_lock(fd)

    def update(self, task_id: UUID, state: TaskState) -> Generator[None, None, None]:
        """Update task state"""
        with self._lock:
            state_data = TaskStateData(state=state, updated=get_current_timestamp())
            self._states.items[task_id] = state_data
            self._dirty.add(task_id)
            self._get_state.cache_clear()
        if self._should_save():
            yield from self.save()

    def get(self, task_id: UUID) -> Generator[TaskStateData, None, None]:
        """Get task state"""
        state = self._get_state(task_id)
        if state is None:
            raise StateNotFoundError(f"State not found: {task_id}")
        yield state

    def cleanup(self, before: datetime) -> Generator[None, None, None]:
        """Remove old states"""
        with self._lock:
            expired = {id_ for id_, state in self._states.items.items() if state.updated < before}
            for id_ in expired:
                del self._states.items[id_]
            self._dirty.update(expired)
            self._get_state.cache_clear()
            yield

        if self._dirty:
            yield from self.save()

    def _should_save(self) -> bool:
        """Check if states should be saved"""
        if not self._dirty:
            return False
        if self._last_save is None:
            return True
        return (get_current_timestamp() - self._last_save).total_seconds() > settings.state.save_interval

    @property
    def modified(self) -> set[UUID]:
        """Get modified task IDs"""
        with self._lock:
            return self._dirty

    @property
    def states(self) -> TaskStates:
        """Get all states"""
        with self._lock:
            return self._states
