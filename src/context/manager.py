from typing import Any

from collections.abc import Generator
from datetime import UTC, datetime
from threading import RLock
from uuid import UUID

from helpers import get_current_timestamp
from src.protocols import ContextManagerProtocol
from src.schemas import Context
from src.core.exceptions import ContextNotFoundError,ContextVersionError


class ContextManager(ContextManagerProtocol):
    """Implementation of context management functionality."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._contexts: dict[UUID, Context] = {}
        self._task_contexts: dict[UUID, UUID] = {}
        self._pipeline_contexts: dict[UUID, UUID] = {}
        self._context_versions: dict[UUID, int] = {}
        self._shared_data: dict[str, Any] = {}

    def create_context(self, pipeline_id: UUID | None = None) -> Generator[None, None, Context]:
        """Create new execution context."""
        context = Context(pipeline_id=pipeline_id)

        with self._lock:
            self._contexts[context.id] = context
            self._context_versions[context.id] = 1
            if pipeline_id:
                self._pipeline_contexts[pipeline_id] = context.id
                context.metadata.pipeline_id = str(pipeline_id)
            yield
            return context.model_copy(deep=True)

    def get_context(self, task_id: UUID) -> Generator[None, None, Context]:
        """Get context by task ID."""
        with self._lock:
            context_id = self._task_contexts.get(task_id)
            if not context_id:
                raise ContextNotFoundError(f"Context not found for task {task_id}")

            context = self._contexts.get(context_id)
            if not context:
                raise ContextNotFoundError(f"Context {context_id} not found")

            yield
            return context.model_copy(deep=True)

    def update_context(self, context: Context) -> Generator[None, None, None]:
        """Update existing context."""
        with self._lock:
            existing = self._contexts.get(context.id)
            if not existing:
                raise ContextNotFoundError(f"Context {context.id} not found")

            current_version = self._context_versions.get(context.id, 0)
            if context.version <= current_version:
                raise ContextVersionError(
                    f"Version conflict. Current: {current_version}, Provided: {context.version}"
                )

            self._record_changes(existing, context)
            self._contexts[context.id] = context
            self._context_versions[context.id] = context.version
            yield

    def cleanup_context(self, pipeline_id: UUID) -> Generator[None, None, None]:
        """Remove context by pipeline ID."""
        with self._lock:
            context_id = self._pipeline_contexts.get(pipeline_id)
            if not context_id:
                raise ContextNotFoundError(f"Context not found for pipeline {pipeline_id}")

            self._cleanup_context_by_id(context_id)
            self._pipeline_contexts.pop(pipeline_id)

            task_ids = [
                task_id for task_id, ctx_id in self._task_contexts.items()
                if ctx_id == context_id
            ]
            for task_id in task_ids:
                self._task_contexts.pop(task_id)
            yield

    def merge_contexts(self, source: Context, target: Context) -> Generator[None, None, Context]:
        """Merge source context into target context."""
        with self._lock:
            new_context = target.model_copy(deep=True)
            new_context.version += 1
            new_context.updated_at = datetime.now(UTC)

            # Merge data and results
            new_context.data.update(source.data)
            new_context.results.update(source.results)

            # Update metadata
            new_context.metadata.merged_from = str(source.id)
            new_context.metadata.merged_at = get_current_timestamp()
            new_context.metadata.source_version = source.version

            self._contexts[new_context.id] = new_context
            self._context_versions[new_context.id] = new_context.version
            yield
            return new_context.model_copy(deep=True)

    def associate_task(self, task_id: UUID, context_id: UUID) -> Generator[None, None, None]:
        """Associate task with context."""
        with self._lock:
            if context_id not in self._contexts:
                raise ContextNotFoundError(f"Context {context_id} not found")

            self._task_contexts[task_id] = context_id
            self._contexts[context_id].metadata.associated_tasks.append(str(task_id))
            yield

    def _cleanup_context_by_id(self, context_id: UUID) -> None:
        """Clean up context and related data."""
        self._contexts.pop(context_id, None)
        self._context_versions.pop(context_id, None)

    def _record_changes(self, old_context: Context, new_context: Context) -> None:
        """Record changes between context versions."""
        changes = {
            "version": self._context_versions[old_context.id],
            "timestamp": datetime.now(UTC),
            "changes": {
                "data": self._diff_dicts(old_context.data, new_context.data),
                "results": self._diff_dicts(old_context.results, new_context.results),
                "metadata": self._diff_dicts(
                    old_context.metadata.model_dump(exclude={"version_history"}),
                    new_context.metadata.model_dump(exclude={"version_history"})
                )
            }
        }
        new_context.metadata.version_history.append(changes)
        new_context.updated_at = get_current_timestamp()

    def _diff_dicts(self, old: dict, new: dict, exclude: set[str] | None = None) -> dict:
        """Compare dictionaries and return changes."""
        exclude = exclude or set()
        changes = {
            "added": {},
            "modified": {},
            "removed": {}
        }

        for key, value in new.items():
            if key in exclude:
                continue
            if key not in old:
                changes["added"][key] = value
            elif old[key] != value:
                changes["modified"][key] = {"old": old[key], "new": value}

        changes["removed"] = {
            k: v for k, v in old.items()
            if k not in new and k not in exclude
        }

        return changes
