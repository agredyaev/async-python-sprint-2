from datetime import datetime, UTC
from typing import Any
from pydantic import BaseModel, Field, model_validator, ConfigDict
from uuid import UUID

from schemas.mixins import CreatedAtMixin, UpdatedAtMixin
from src.schemas.mixins import StartedAtMixin, CurrentTimestampMixin


class TaskResult(StartedAtMixin):
    """Task execution result data."""
    task_id: UUID = Field(..., description="Task identifier")
    success: bool = Field(True, description="Execution success flag")
    result: Any | None = Field(None, description="Task result data")
    error: str | None = Field(None, description="Error message if failed")
    completed_at: datetime | None = Field(None, description="Execution completion time")
    
    model_config = ConfigDict(frozen=False, validate_assignment=True)
    
    @property
    def execution_time(self) -> float | None:
        """Returns execution time in seconds if task completed."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class ResourceUsage(BaseModel):
    """Resource usage metrics."""
    cpu_percent: float = Field(0.0, ge=0.0, le=100.0, description="CPU usage percentage")
    memory_mb: float = Field(0.0, ge=0.0, description="Memory usage in megabytes")
    disk_reads: int = Field(0, ge=0, description="Number of disk read operations")
    disk_writes: int = Field(0, ge=0, description="Number of disk write operations")
    network_rx_bytes: int = Field(0, ge=0, description="Bytes received over network")
    network_tx_bytes: int = Field(0, ge=0, description="Bytes transmitted over network")

    model_config = ConfigDict(frozen=False, validate_assignment=True)


class MetricRecord(CurrentTimestampMixin):
    """Individual metric measurement."""
    name: str = Field(..., min_length=1, description="Metric name")
    value: float = Field(..., description="Metric value")
    labels: dict[str, str] = Field(default_factory=dict, description="Metric labels")

    model_config = ConfigDict(frozen=False, validate_assignment=True)


class TaskMetrics(CreatedAtMixin, UpdatedAtMixin):
    """Detailed task execution metrics."""
    execution_time: float = Field(default=0.0, ge=0.0, description="Total execution time in seconds")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    error_count: int = Field(default=0, ge=0, description="Number of errors occurred")
    last_error: str | None = Field(None, description="Last error message")
    resource_usage: ResourceUsage = Field(..., description="Resource usage metrics")
    measurements: list[MetricRecord] = Field(default_factory=list, description="Detailed metric measurements")

    model_config = ConfigDict(frozen=False, validate_assignment=True)

    def add_measurement(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Add new metric measurement."""
        self.measurements.append(
            MetricRecord(
                name=name,
                value=value,
                labels=labels or {},
                timestamp=datetime.now(tz=UTC)
            )
        )
        self.updated_at = datetime.now(tz=UTC)


class RetryPolicy(BaseModel):
    """Task retry policy configuration."""
    max_retries: int = Field(default=60, ge=0, description="Maximum number of retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.0, description="Delay between retries in seconds")
    max_delay: float = Field(default=300.0, ge=0.0, description="Maximum retry delay in seconds")
    exponential_backoff: bool = Field(default=True, description="Use exponential backoff for retries")
    retry_on_exceptions: list[str] = Field(
        default_factory=list,
        description="List of exception names to retry on"
    )

    model_config = ConfigDict(frozen=True)

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given retry attempt."""
        if not self.exponential_backoff:
            return self.retry_delay

        delay = self.retry_delay * (2 ** (attempt - 1))
        return min(delay, self.max_delay)


class TaskTimeout(BaseModel):
    """Task timeout configuration."""
    total: float = Field(..., gt=0.0, description="Total execution timeout in seconds")
    operation: float | None = Field(None, gt=0.0, description="Individual operation timeout")
    kill_on_timeout: bool = Field(True, description="Kill task on timeout")

    model_config = ConfigDict(frozen=True)

    @model_validator(mode='after')
    def validate_timeouts(self) -> 'TaskTimeout':
        """Validate that operation timeout doesn't exceed total timeout."""
        if self.operation and self.operation > self.total:
            raise ValueError("Operation timeout cannot exceed total timeout")
        return self


class ExecutionPriority(BaseModel):
    """Task execution priority settings."""
    initial: int = Field(default=0, description="Initial task priority")
    min_priority: int = Field(default=-100, description="Minimum priority value")
    max_priority: int = Field(default=100, description="Maximum priority value")
    age_boost: float = Field(
        default=0.0,
        description="Priority boost per second of waiting"
    )
    retry_penalty: float = Field(
        default=0.0,
        description="Priority penalty per retry attempt"
    )

    model_config = ConfigDict(frozen=True)

    def calculate_priority(
        self,
        wait_time: float,
        retry_count: int = 0
    ) -> int:
        """Calculate current priority based on wait time and retries."""
        priority = (
            self.initial +
            (wait_time * self.age_boost) -
            (retry_count * self.retry_penalty)
        )
        return max(min(int(priority), self.max_priority), self.min_priority)