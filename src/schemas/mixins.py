from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.helpers import get_current_timestamp


class BaseMixin(BaseModel):
    model_config = {"json_encoders": {datetime: lambda dt: dt.isoformat()}}


class UUIDMixin(BaseMixin):
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")


class CreatedAtMixin(BaseMixin):
    created_at: datetime = Field(default_factory=get_current_timestamp, description="Creation time")


class UpdatedAtMixin(BaseMixin):
    updated_at: datetime = Field(default_factory=get_current_timestamp, description="Update time")


class StartedAtMixin(BaseMixin):
    started_at: datetime = Field(default_factory=get_current_timestamp, description="Execution start time")


class CurrentTimestampMixin(BaseMixin):
    timestamp: datetime = Field(default_factory=get_current_timestamp, description="Measurement time")
