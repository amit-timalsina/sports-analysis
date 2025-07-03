from datetime import datetime
from uuid import UUID

from pydantic import Field

from common.schemas import AppBaseModel
from common.schemas.entry_type import EntryType


class ActivityEntryBase(AppBaseModel):
    """Base schema for all activity entries."""

    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    conversation_id: UUID = Field(..., description="ID of the related conversation")
    entry_type: EntryType = Field(..., description="Type of entry")
    original_transcript: str = Field(..., description="Original voice transcript")
    overall_confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score",
    )
    mental_state: str = Field(..., description="Mental state during activity")
    activity_timestamp: datetime | None = Field(None, description="When the activity occurred")
