import os

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from polyfactory.factories.pydantic_factory import ModelFactory
from pytest_mock import MockerFixture

from src.core.exceptions import StateLoadError, StateLockError, StateNotFoundError, StateSaveError
from src.schemas import StateData, TaskState, TaskStateData, TaskStates


class BaseFactory:
    __random_seed__ = 1


class TaskStateDataFactory(BaseFactory, ModelFactory[TaskStateData]): ...


class StateDataFactory(BaseFactory, ModelFactory[StateData]): ...


@pytest.fixture
def state_manager(mocker: MockerFixture):
    mocker.patch("pathlib.Path.mkdir")
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("os.open", return_value=999)
    mocker.patch("os.close")
    mocker.patch("fcntl.flock")

    from src.state.manager import FileStateManager

    return FileStateManager()


@pytest.fixture
def mock_timestamp(mocker):
    return mocker.patch("src.helpers.get_current_timestamp", return_value=datetime.now(tz=UTC))


class TestFileStateManager:
    def test_init(self, state_manager):
        assert isinstance(state_manager._states, TaskStates) or isinstance(
            state_manager._states, dict
        ), "States should be of type TaskStates or dict"
        assert isinstance(state_manager._dirty, set), "Dirty should be of type set"
        assert state_manager._last_save is None, "Last save should be None"

    def test_context_manager(self, state_manager, mocker):
        mock_save = mocker.patch.object(state_manager, "save")
        with state_manager:
            state_manager._dirty.add(uuid4())
        mock_save.assert_called_once()

    def test_validate_version_success(self, state_manager):
        state_manager._validate_version(1)

    def test_validate_version_failure(self, state_manager):
        with pytest.raises(StateLoadError):
            state_manager._validate_version(999)

    def test_update_state(self, state_manager, mock_timestamp, mocker):
        task_id = uuid4()
        state = TaskState.RETRY_PENDING

        for _ in state_manager.update(task_id, state):
            continue

        assert state_manager.states.items[task_id].state == state, "State should be updated"
        assert state_manager._get_state.cache_info().currsize == 0, "Cache should be cleared"

    def test_get_state(self, state_manager):
        task_id = uuid4()
        state_data = TaskStateDataFactory.build()
        state_manager._states.items[task_id] = state_data

        result = next(state_manager.get(task_id))
        assert result == state_data

    def test_get_state_not_found(self, state_manager):
        with pytest.raises(StateNotFoundError):
            next(state_manager.get(uuid4()))

    def test_cleanup(self, state_manager, mock_timestamp, mocker):
        save_mock = mocker.patch.object(state_manager, "save")

        old_task_id = uuid4()
        old_timestamp = datetime.now(tz=UTC) - timedelta(days=2)
        state_manager._states.items[old_task_id] = TaskStateData(state=TaskState.COMPLETED, updated=old_timestamp)

        new_task_id = uuid4()
        state_manager._states.items[new_task_id] = TaskStateData(state=TaskState.PENDING, updated=datetime.now(tz=UTC))

        cleanup_before = datetime.now(tz=UTC) - timedelta(days=1)
        for _ in state_manager.cleanup(cleanup_before):
            continue

        assert old_task_id not in state_manager.states.items, "Old task should be removed"
        assert new_task_id in state_manager.states.items, "New task should not be removed"
        save_mock.assert_called_once()

    def test_acquire_lock(self, state_manager, mocker):
        mock_open = mocker.patch("os.open", return_value=999)
        mock_flock = mocker.patch("fcntl.flock")

        fd = state_manager._acquire_lock(Path("/tmp/test_acquire.lock"))
        assert fd == 999, "File descriptor should be returned"
        mock_flock.assert_called_once()

    def test_acquire_lock_error(self, state_manager, mocker):
        mocker.patch("os.open", side_effect=OSError)

        with pytest.raises(StateLockError):
            state_manager._acquire_lock(Path("/tmp/test.lock"))

    def test_save_state(self, state_manager, mocker):
        mock_write = mocker.patch("pathlib.Path.write_text")
        mock_replace = mocker.patch("pathlib.Path.replace")

        state_manager._dirty.add(uuid4())

        for _ in state_manager.save():
            continue

        assert mock_write.called, "File should be written"
        assert mock_replace.called, "File should be replaced"
        assert not state_manager._dirty, "Dirty set should be cleared"

    def test_load_state(self, state_manager, mocker):
        test_data = StateDataFactory.build()
        test_data.version = 1
        mocker.patch("pathlib.Path.read_text", return_value=test_data.model_dump_json())

        for _ in state_manager.load():
            continue

        assert state_manager.states == test_data.states

    def test_should_save(self, state_manager, mock_timestamp):
        assert not state_manager._should_save(), "Should not save if dirty set is empty"

        state_manager._dirty.add(uuid4()), "Dirty set should not be empty"
        assert state_manager._should_save(), "Should save if dirty set is not empty"

        state_manager._last_save = datetime.now(tz=UTC) - timedelta(seconds=61)
        assert state_manager._should_save(), "Should save if last save is older than 60 seconds"
