from idlelib.configdialog import changes
from uuid import UUID, uuid4

import pytest

from polyfactory.factories.pydantic_factory import ModelFactory
from pytest_mock import MockerFixture

from src.context import ContextManager
from src.core.exceptions import ContextNotFoundError, ContextVersionError
from src.helpers import get_current_timestamp
from src.schemas import Context, TaskConfig


class BaseFactory:
    __random_seed__ = 1


class ContextFactory(BaseFactory, ModelFactory[Context]):
    pass


@pytest.fixture
def context_manager():
    return ContextManager()


@pytest.fixture
def mock_get_current_timestamp(mocker: MockerFixture):
    return mocker.patch("src.helpers.get_current_timestamp", return_value=get_current_timestamp())


class TestContextManager:
    def test_create_context(self, context_manager: ContextManager):
        """Test creating a new context."""
        for _ in context_manager.create_context():
            continue
        assert isinstance(context_manager, ContextManager), "Context is not an instance of Context"
        assert len(context_manager._contexts.contexts) == 1, "Context was not created"

    def test_create_context_with_pipeline_id(self, context_manager: ContextManager):
        """Test creating a new context with pipeline ID."""
        pipeline_id = uuid4()
        for _ in context_manager.create_context(pipeline_id):
            continue
        assert pipeline_id in [
            ctx.pipeline_id for _, ctx in context_manager._contexts.contexts.items()
        ], "Pipeline ID not set"

    def test_get_context(self, context_manager: ContextManager):
        """Test retrieving a context by task ID."""
        task_id = uuid4()
        ctx_build = ContextFactory.build()
        context_manager._task_contexts.task_contexts[task_id] = ctx_build.id
        context_manager._contexts.contexts[ctx_build.id] = ctx_build

        ctx = context_manager.get_context(task_id)
        assert ctx is not None, "Context not found"
        assert ctx.id == ctx_build.id, "Created context ID does not match"

    def test_get_context_not_found(self, context_manager: ContextManager):
        """Test retrieving a non-existent context."""
        with pytest.raises(ContextNotFoundError), context_manager.get_context(uuid4()):
            pass

    def test_update_context(self, context_manager: ContextManager, mock_get_current_timestamp):
        """Test updating an existing context."""
        context = ContextFactory.build()
        context_manager._contexts.contexts[context.id] = context

        updated_context = context.model_copy(deep=True)
        updated_context.data["new_key"] = "new_value"
        updated_context.update_version()

        for _ in context_manager.update_context(updated_context):
            continue

        assert context_manager._contexts.contexts[context.id].data["new_key"] == "new_value", "Data not updated"
        assert context_manager._contexts.contexts[context.id].version == updated_context.version, "Version not updated"
        assert context_manager._contexts.contexts[context.id].updated_at != context.updated_at, "Timestamp not updated"

    def test_update_context_version_conflict(self, context_manager: ContextManager):
        """Test updating a context with version conflict."""
        context = ContextFactory.build()
        context_manager._contexts.contexts[context.id] = context
        context.version -= 1

        with pytest.raises(
            ContextVersionError, match=f"Version conflict. Current: {context.version}, Provided: {context.version}"
        ):
            next(context_manager.update_context(context))

    def test_cleanup_context(self, context_manager: ContextManager):
        """Test removing a context and associated data."""
        pipeline_id = uuid4()
        context = ContextFactory.build()
        task_id = uuid4()

        context_manager._pipeline_contexts.pipeline_contexts[pipeline_id] = context.id
        context_manager._contexts.contexts[context.id] = context
        context_manager._task_contexts.task_contexts[task_id] = context.id

        for _ in context_manager.cleanup_context(pipeline_id):
            continue

        assert pipeline_id not in context_manager._pipeline_contexts.pipeline_contexts
        assert context.id not in context_manager._contexts.contexts
        assert task_id not in context_manager._task_contexts.task_contexts

    def test_cleanup_context_not_found(self, context_manager: ContextManager):
        """Test cleaning up a non-existent context."""
        pipeline_id = uuid4()

        with pytest.raises(ContextNotFoundError, match=f"Context not found for pipeline {pipeline_id}"):
            next(context_manager.cleanup_context(pipeline_id))

    def test_merge_contexts(self, context_manager: ContextManager, mock_get_current_timestamp):
        """Test merging two contexts."""
        source = ContextFactory.build(data={"key1": "value1"}, results={"result1": "res1"})
        target = ContextFactory.build(data={"key2": "value2"}, results={"result2": "res2"})

        for _ in context_manager.merge_contexts(source, target):
            continue

        merged = context_manager._contexts.contexts[target.id]
        assert merged.data == {"key1": "value1", "key2": "value2"}, "Data not merged"
        assert merged.results == {"result1": "res1", "result2": "res2"}, "Results not merged"
        assert merged.metadata.merged_from == str(source.id), "Merged from not set"
        assert merged.metadata.source_version == source.version, "Source version not set"
        assert merged.version == target.version + 1, "Version not incremented"
        assert merged.updated_at != target.updated_at, "Timestamp not updated"

    def test_associate_task(self, context_manager: ContextManager):
        """Test associating a task with a context."""
        task_id = uuid4()
        context = ContextFactory.build()
        context_manager._contexts.contexts[context.id] = context

        for _ in context_manager.associate_task(task_id, context.id):
            continue

        assert context_manager._task_contexts.task_contexts[task_id] == context.id, "Task not associated"
        assert (
            str(task_id) in context_manager._contexts.contexts[context.id].metadata.associated_tasks
        ), "Task not recorded"

    def test_associate_task_context_not_found(self, context_manager: ContextManager):
        """Test associating a task with a non-existent context."""
        task_id = uuid4()
        contest_id = uuid4()
        with pytest.raises(ContextNotFoundError, match=f"Context {contest_id} not found"):
            next(context_manager.associate_task(task_id, contest_id))
