from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

from src.schemas import TaskState


class TaskStateData(BaseModel):
    """Single task state data"""

    state: TaskState
    updated: datetime


class TaskStates(BaseModel):
    """Collection of task states"""

    items: dict[UUID, TaskStateData] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class StateData(BaseModel):
    """State file data structure"""

    version: int
    updated: datetime
    states: TaskStates
