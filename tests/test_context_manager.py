from uuid import uuid4

import pytest

from polyfactory.factories.pydantic_factory import ModelFactory
from pytest_mock import MockerFixture

from src.context import ContextManager
from src.schemas import Context, ContextMetadata, TaskConfig


class BaseFactory:
    __random_seed__ = 1


class ContextFactory(BaseFactory, ModelFactory[Context]): ...


class TaskConfigFactory(BaseFactory, ModelFactory[TaskConfig]): ...


@pytest.fixture
def mock_context_manager(mocker: MockerFixture):
    return mocker.create_autospec(ContextManager)


@pytest.fixture
def context_manager():
    return ContextManager()


def test_create_new_context(context_manager: ContextManager):
    task_config = TaskConfigFactory.build()

    new_context = context_manager.create_context(task_config)

    assert isinstance(new_context, Context)
    assert new_context.pipeline_id is None
    assert new_context.data == {}
    assert new_context.results == {}
    assert isinstance(new_context.metadata, ContextMetadata)


def test_get_existing_context(context_manager: ContextManager, mocker: MockerFixture):
    context_id = uuid4()
    existing_context = ContextFactory.build(id=context_id)
    mocker.patch.object(context_manager, "get_context", return_value=existing_context)

    retrieved_context = context_manager.get_context(context_id)

    assert retrieved_context == existing_context
    assert retrieved_context.id == context_id


def test_update_context_data(context_manager: ContextManager):
    context = ContextFactory.build()
    task_config = TaskConfigFactory.build()
    new_data = {"key": "value"}
    context_manager.update_context(context, new_data)

    assert context.data["key"] == "value"


def test_context_version_update_on_change(context_manager: ContextManager):
    context = ContextFactory.build(version=1)

    new_data = {"new_key": "new_value"}
    context_manager.update_context(context, new_data)

    assert context.version == 2


def test_merge_contexts(context_manager: ContextManager):
    context1 = ContextFactory.build(data={"a": 1})
    context2 = ContextFactory.build(data={"b": 2})

    context_manager.merge_contexts(context1, context2)

    assert context1.data == {"a": 1, "b": 2}


def test_context_persists_after_task(context_manager: ContextManager, mocker: MockerFixture):
    task_config = TaskConfigFactory.build()
    context = ContextFactory.build()

    mock_task = mocker.Mock()
    mock_task.execute.return_value = None

    context_manager.execute_task_in_context(task_config, mock_task)

    mock_task.execute.assert_called_once_with(context)
    assert context_manager.get_context(context.id) == context
