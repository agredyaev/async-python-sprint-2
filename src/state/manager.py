from functools import lru_cache
from typing import Generator, Set
from threading import RLock
from datetime import datetime
from uuid import UUID
import json
import os
from pathlib import Path
import fcntl
import time
from contextlib import contextmanager

from helpers import get_current_timestamp
from src.schemas import TaskState
from core.settings import settings
from src.protocols import StateManagerProtocol
from src.core.exceptions import StateFileError,StateError,StateValidationError


class FileStateManager(StateManagerProtocol):
    def __init__(self) -> None:
        self._config = settings.scheduler
        self._lock = RLock()
        self._states: dict[UUID, TaskState] = {}
        self._modified_states: Set[UUID] = set()
        self._state_file = settings.scheduler.state_file
        self._lock_file = self._state_file
        self._last_save_time: datetime | None = None
        self._state_cache = lru_cache(maxsize=100)(self._get_state_from_storage)

    @contextmanager
    def _file_lock(self, timeout: float = 10.0) -> Generator[int, None, None]:
        lock_fd = None
        start_time = time.monotonic()
        try:
            while True:
                try:
                    if not self._lock_file.exists():
                        self._lock_file.touch()
                    lock_fd = os.open(str(self._lock_file), os.O_RDWR)
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except (IOError, OSError) as e:
                    if time.monotonic() - start_time > timeout:
                        raise StateFileError(f"Failed to acquire file lock after {timeout} seconds") from e
                    time.sleep(0.1)
            yield lock_fd
        finally:
            if lock_fd is not None:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    os.close(lock_fd)
                except (IOError, OSError):
                    pass

    def _get_state_from_storage(self, task_id: UUID) -> TaskState | None:
        return self._states.get(task_id)

    def save_state(self) -> Generator[None, None, None]:
        if not self._modified_states:
            yield
            return

        try:
            with self._lock:
                state_data = {
                    'version': 1,
                    'timestamp': get_current_timestamp().isoformat(),
                    'states': {str(task_id): state.value for task_id, state in self._states.items()}
                }
            yield

            yield from self._create_backup()

            with self._file_lock() as _:
                temp_file = self._state_file.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(state_data, f, indent=2)
                yield
                temp_file.replace(self._state_file)
                yield

            with self._lock:
                self._modified_states.clear()
                self._last_save_time = get_current_timestamp()
        except Exception as e:
            raise StateFileError(f"Failed to save state: {str(e)}") from e

    def load_state(self) -> Generator[None, None, None]:
        if not self._state_file.exists():
            yield
            return

        try:
            with self._file_lock() as _:
                yield from self._validate_state_file()
                with open(self._state_file, 'r') as f:
                    state_data = json.load(f)
                yield

            with self._lock:
                self._states = {UUID(task_id): TaskState(value=state) for task_id, state in state_data.get('states', {}).items()}
                self._modified_states.clear()
            yield
        except json.JSONDecodeError as e:
            raise StateFileError(f"Invalid state file format: {str(e)}") from e
        except Exception as e:
            raise StateFileError(f"Failed to load state: {str(e)}") from e

    def update_task_state(self, task_id: UUID, state: TaskState) -> Generator[None, None, None]:
        if not isinstance(state, TaskState):
            raise StateValidationError(f"Invalid state type: {type(state)}")

        with self._lock:
            current_state = self._states.get(task_id)
            if current_state != state:
                self._states[task_id] = state
                self._modified_states.add(task_id)
                self._state_cache.cache_clear()
            yield

        if (self._last_save_time is None or
            (get_current_timestamp() - self._last_save_time).total_seconds() > self._config.state_check_interval):
            yield from self.save_state()

    def get_task_state(self, task_id: UUID) -> Generator[None, None, TaskState]:
        state = self._state_cache(task_id)
        if state is None:
            raise StateError(f"State not found for task {task_id}")
        yield
        return state

    def cleanup_states(self, older_than: datetime) -> Generator[None, None, None]:
        yield from self._cleanup_memory_states(older_than)
        yield from self._cleanup_backup_files(older_than)

    def _cleanup_memory_states(self, older_than: datetime) -> Generator[None, None, None]:
        with self._lock:
            yield

    def _cleanup_backup_files(self, older_than: datetime) -> Generator[None, None, None]:
        try:
            backup_pattern = self._state_file.with_suffix('.bak.*')
            for backup_file in Path(self._state_file.parent).glob(str(backup_pattern)):
                try:
                    timestamp_str = backup_file.suffix[1:]
                    file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    if file_time < older_than:
                        backup_file.unlink()
                    yield
                except (ValueError, OSError):
                    continue
        except Exception as e:
            print(f"Error cleaning up backup files: {str(e)}")
            yield

    def _create_backup(self) -> Generator[None, None, None]:
        if self._state_file.exists():
            try:
                backup_file = self._state_file.with_suffix(f'.bak.{get_current_timestamp().strftime("%Y%m%d_%H%M%S")}')
                import shutil
                shutil.copy2(self._state_file, backup_file)
                yield
            except Exception as e:
                print(f"Warning: Failed to create state file backup: {str(e)}")
                yield

    def _validate_state_file(self) -> Generator[None, None, None]:
        try:
            with open(self._state_file, 'r') as f:
                state_data = json.load(f)
            yield

            required_fields = {'version', 'timestamp', 'states'}
            if not all(field in state_data for field in required_fields):
                raise StateFileError("Invalid state file: missing required fields")
            yield

            if state_data['version'] != 1:
                raise StateFileError(f"Unsupported state file version: {state_data['version']}")
            yield

            try:
                datetime.fromisoformat(state_data['timestamp'])
            except ValueError as e:
                raise StateFileError("Invalid timestamp format") from e
            yield
        except json.JSONDecodeError as e:
            raise StateFileError(f"Invalid state file format: {str(e)}") from e
        except Exception as e:
            raise StateFileError(f"Failed to validate state file: {str(e)}") from e

    def get_modified_task_ids(self) -> Set[UUID]:
        with self._lock:
            return set(self._modified_states)

    def has_modified_states(self) -> bool:
        return bool(self._modified_states)

    def get_all_states(self) -> dict[UUID, TaskState]:
        with self._lock:
            return dict(self._states)