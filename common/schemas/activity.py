from uuid import UUID

from pydantic import Field

from common.schemas import AppBaseModel
from fitness_tracking.schemas.enums.activity_type import ActivityType


class ActivityEntryBase(AppBaseModel):
    """Base schema for all activity entries."""

    conversation_id: UUID = Field(..., description="ID of the related conversation")
    activity_type: ActivityType = Field(..., description="Type of activity")
    mental_state: str = Field(..., description="Mental state during activity")
    energy_level: int | None = Field(None, description="Energy level during activity")
    notes: str | None = Field(None, description="Notes about the activity")
