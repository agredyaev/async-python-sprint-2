from types import TracebackType
from typing import Any

from collections.abc import Generator
from threading import RLock
from uuid import UUID

from src.core.exceptions import ContextNotFoundError, ContextVersionError
from src.core.logger import get_logger
from src.helpers import get_current_timestamp
from src.protocols import ContextManagerProtocol
from src.schemas import ChangeSet, Context, ContextStore, DictDiff, PipelineContextMap, TaskContextMap, VersionHistory

logger = get_logger("context_manager")


class ContextManager(ContextManagerProtocol):
    """Manages execution contexts for task scheduling system."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._contexts = ContextStore()
        self._task_contexts = TaskContextMap()
        self._pipeline_contexts = PipelineContextMap()

    def __enter__(self) -> "ContextManager":
        """Context manager entry"""
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        """Context manager exit."""
        logger.info("Exiting context manager")

    def create_context(self, pipeline_id: UUID | None = None) -> Generator[Context, None, None]:
        """
        Create a new context.

        Args:
            pipeline_id: Optional UUID of the associated pipeline.

        Yields:
            None

        Returns:
            Newly created Context object.
        """
        context = Context(pipeline_id=pipeline_id)
        with self._lock:
            self._contexts.contexts[context.id] = context
            if pipeline_id:
                self._pipeline_contexts.pipeline_contexts[pipeline_id] = context.id
                context.metadata.pipeline_id = str(pipeline_id)
            yield context.model_copy(deep=True)

    def get_context(self, task_id: UUID) -> Context:
        """
        Retrieve context by task ID.

        Args:
            task_id: UUID of the task.

        Yields:
            None

        Returns:
            Associated Context object.

        Raises:
            ContextNotFoundError: If context not found.
        """
        with self._lock:
            context_id = self._task_contexts.task_contexts.get(task_id)
            if not context_id or context_id not in self._contexts.contexts:
                raise ContextNotFoundError(f"Context not found for task {task_id}")

            return self._contexts.contexts[context_id].model_copy(deep=True)

    def update_context(self, context: Context) -> Generator[None, None, None]:
        """
        Update existing context.

        Args:
            context: Updated Context object.

        Yields:
            None

        Raises:
            ContextNotFoundError: If context not found.
            ContextVersionError: If version conflict occurs.
        """
        with self._lock:
            existing = self._contexts.contexts.get(context.id)
            if not existing:
                raise ContextNotFoundError(f"Context {context.id} not found")
            if context.version <= existing.version:
                raise ContextVersionError(f"Version conflict. Current: {existing.version}, Provided: {context.version}")
            self._record_changes(existing, context)
            context.update_version()
            self._contexts.contexts[context.id] = context
            yield

    def cleanup_context(self, pipeline_id: UUID) -> Generator[None, None, None]:
        """
        Remove context and associated data by pipeline ID.

        Args:
            pipeline_id: UUID of the pipeline.

        Yields:
            None

        Raises:
            ContextNotFoundError: If context not found.
        """
        with self._lock:
            context_id = self._pipeline_contexts.pipeline_contexts.get(pipeline_id)
            if not context_id:
                raise ContextNotFoundError(f"Context not found for pipeline {pipeline_id}")
            self._contexts.contexts.pop(context_id, None)
            self._pipeline_contexts.pipeline_contexts.pop(pipeline_id)
            self._task_contexts.task_contexts = {
                task_id: ctx_id for task_id, ctx_id in self._task_contexts.task_contexts.items() if ctx_id != context_id
            }
            yield

    def merge_contexts(self, source: Context, target: Context) -> Generator[Context, None, None]:
        """
        Merge source context into target context.

        Args:
            source: Source Context object.
            target: Target Context object.

        Yields:
            None

        Returns:
            Merged Context object.
        """

        with self._lock:
            new_context = target.model_copy(deep=True)
            new_context.data.update(source.data)
            new_context.results.update(source.results)
            new_context.metadata.merged_from = str(source.id)
            new_context.metadata.merged_at = get_current_timestamp()
            new_context.metadata.source_version = source.version
            new_context.update_version()
            self._contexts.contexts[new_context.id] = new_context
            yield new_context.model_copy(deep=True)

    def associate_task(self, task_id: UUID, context_id: UUID) -> Generator[None, None, None]:
        """
        Associate task with context.

        Args:
            task_id: UUID of the task.
            context_id: UUID of the context.

        Yields:
            None

        Raises:
            ContextNotFoundError: If context not found.
        """
        with self._lock:
            if context_id not in self._contexts.contexts:
                raise ContextNotFoundError(f"Context {context_id} not found")
            self._task_contexts.task_contexts[task_id] = context_id
            self._contexts.contexts[context_id].metadata.associated_tasks.append(str(task_id))
            yield

    def _record_changes(self, old_context: Context, new_context: Context) -> None:
        changes = VersionHistory(
            version=old_context.version,
            timestamp=get_current_timestamp(),
            changes=ChangeSet(
                data=self._diff_dicts(old_context.data, new_context.data),
                results=self._diff_dicts(old_context.results, new_context.results),
                metadata=self._diff_dicts(
                    old_context.metadata.model_dump(exclude={"version_history"}),
                    new_context.metadata.model_dump(exclude={"version_history"}),
                ),
            ),
        )
        new_context.metadata.version_history.append(changes)
        new_context.updated_at = get_current_timestamp()

    @staticmethod
    def _diff_dicts(old: dict[str, Any], new: dict[str, Any]) -> DictDiff:
        diff = DictDiff()
        for key, value in new.items():
            if key not in old:
                diff.added[key] = value
            elif old[key] != value:
                diff.modified[key] = {"old": old[key], "new": value}
        diff.removed = {k: v for k, v in old.items() if k not in new}
        return diff

    @property
    def contexts(self) -> dict[UUID, Context]:
        return self._contexts.contexts

    @property
    def task_contexts(self) -> dict[UUID, UUID]:
        return self._task_contexts.task_contexts

    @property
    def pipeline_contexts(self) -> dict[UUID, UUID]:
        return self._pipeline_contexts.pipeline_contexts
