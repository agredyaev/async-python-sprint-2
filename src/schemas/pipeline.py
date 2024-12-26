from pydantic import ConfigDict, Field, computed_field, model_validator

from src.core.settings import settings
from src.schemas.mixins import UUIDMixin
from src.task.base import BaseTask


class Pipeline(UUIDMixin):
    """Configuration for task pipeline execution."""

    tasks: list[BaseTask] = Field(..., min_length=1, description="List of pipeline tasks")
    max_parallel: int = Field(settings.pipeline.max_parallel, description="Maximum parallel tasks")
    timeout: float = Field(settings.pipeline.timeout, description="Pipeline timeout in seconds")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @computed_field
    def task_count(self) -> int:
        """Returns the total number of tasks in pipeline."""
        return len(self.tasks)

    @model_validator(mode="after")
    def validate_tasks(self) -> "Pipeline":
        """Validates task list is not empty."""
        if not self.tasks:
            raise ValueError("Pipeline must contain at least one task")
        return self
