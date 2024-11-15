from typing import Any

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from src.helpers import get_current_timestamp
from src.schemas.mixins import CreatedAtMixin, UpdatedAtMixin, UUIDMixin


class ContextMetadata(CreatedAtMixin, UpdatedAtMixin):
    """Metadata model for context."""

    version_history: list[dict[str, Any]] = Field(default_factory=list)
    pipeline_id: str | None = None
    associated_tasks: list[str] = Field(default_factory=list)
    merged_from: str | None = None
    merged_at: datetime | None = None
    source_version: int | None = None


class Context(UUIDMixin, CreatedAtMixin, UpdatedAtMixin):
    """Task execution context containing runtime data and results."""

    pipeline_id: UUID | None = Field(None, description="Pipeline identifier if task is part of pipeline")
    data: dict[str, Any] = Field(default_factory=dict, description="Context data")
    results: dict[str, Any] = Field(default_factory=dict, description="Execution results")
    metadata: ContextMetadata = Field(default_factory=ContextMetadata, description="Context metadata")
    version: int = Field(default=1, ge=1, description="Context version number")

    model_config = ConfigDict(frozen=False, validate_assignment=True)

    def update_version(self) -> None:
        """Updates context version and timestamp."""
        self.version += 1
        self.updated_at = get_current_timestamp()
