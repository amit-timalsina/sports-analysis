"""Base database models and mixins."""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, func
from sqlmodel import Column, Field, SQLModel


class BaseTable(SQLModel):
    """Base table model with common fields."""

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )


class VoiceProcessingMixin(SQLModel):
    """Mixin for voice processing metadata."""

    # Voice processing metadata
    transcript: str = Field(description="Original voice transcript")
    confidence_score: float = Field(ge=0.0, le=1.0, description="AI confidence in data extraction")
    processing_duration: float | None = Field(
        default=None,
        description="Time taken to process in seconds",
    )


class UserSessionMixin(SQLModel):
    """Mixin for user and session information."""

    user_id: str = Field(index=True, description="User identifier")
    session_id: str = Field(index=True, description="Voice session identifier")


class EntryType(str, Enum):
    """Types of entries in the system."""

    FITNESS = "fitness"
    CRICKET_COACHING = "cricket_coaching"
    CRICKET_MATCH = "cricket_match"
    REST_DAY = "rest_day"


class CommonEntryFields(SQLModel):
    """Common fields for all entry types."""

    entry_type: EntryType = Field(index=True, description="Type of entry")
    mental_state: str = Field(description="Mental state during activity")
    notes: str | None = Field(default=None, description="Additional notes")
