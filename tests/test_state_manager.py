from pathlib import Path
from unittest.mock import mock_open

import pytest

from polyfactory.factories.pydantic_factory import ModelFactory
from pytest_mock import MockerFixture

from src.core.exceptions import StateFileError, StateValidationError
from src.schemas import Context
from src.state import FileStateManager


class ContextFactory(ModelFactory[Context]):
    __random_seed__ = 1


@pytest.fixture
def state_manager(mocker: MockerFixture) -> FileStateManager:
    mocker.patch("src.core.settings.settings.scheduler.state_file_path", new=Path("/fake/path/state.lock"))
    return FileStateManager()


def test_save_state_to_lock_file(state_manager: FileStateManager, mocker: MockerFixture):
    context = ContextFactory.build()
    mock_open_func = mock_open()
    mocker.patch("builtins.open", mock_open_func)

    state_manager.save_state(context)

    mock_open_func.assert_called_once_with(Path("/fake/path/state.lock"), "wb")
    mock_open_func().write.assert_called_once()


def test_load_state_from_lock_file(state_manager: FileStateManager, mocker: MockerFixture):
    context = ContextFactory.build()
    serialized_context = context.model_dump(mode="json").encode("utf-8")

    mock_open_func = mock_open(read_data=serialized_context)
    mocker.patch("builtins.open", mock_open_func)

    loaded_context = state_manager.load_state()

    assert loaded_context == context


def test_load_state_lock_file_not_found(state_manager: FileStateManager, mocker: MockerFixture):
    mocker.patch("pathlib.Path.exists", return_value=False)

    loaded_context = state_manager.load_state()

    assert loaded_context is None


def test_save_state_lock_file_error(state_manager: FileStateManager, mocker: MockerFixture):
    context = ContextFactory.build()

    mock_open_func = mock_open()
    mock_open_func.side_effect = OSError("Unable to write to file")

    mocker.patch("builtins.open", mock_open_func)

    with pytest.raises(StateFileError, match="Unable to write to file"):
        state_manager.save_state(context)


def test_load_state_lock_file_error(state_manager: FileStateManager, mocker: MockerFixture):
    mock_open_func = mock_open()
    mock_open_func.side_effect = OSError("Unable to read file")

    mocker.patch("builtins.open", mock_open_func)

    with pytest.raises(StateFileError, match="Unable to read file"):
        state_manager.load_state()


def test_load_state_invalid_data_in_lock_file(state_manager: FileStateManager, mocker: MockerFixture):
    mock_open_func = mock_open(read_data=b"{invalid_binary_data}")

    mocker.patch("builtins.open", mock_open_func)

    with pytest.raises(StateValidationError, match="Invalid data format"):
        state_manager.load_state()


def test_save_and_load_state_integration_with_lock_file(state_manager: FileStateManager, mocker: MockerFixture):
    context = ContextFactory.build()

    state_manager.save_state(context)

    mock_open_func = mock_open(read_data=context.model_dump(mode="json").encode("utf-8"))
    mocker.patch("builtins.open", mock_open_func)

    loaded_context = state_manager.load_state()

    assert loaded_context == context
