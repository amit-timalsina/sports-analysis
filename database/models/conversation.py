"""Database models for conversation persistence."""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, DateTime, func
from sqlmodel import Column, Field, Relationship, SQLModel


class ConversationState(str, Enum):
    """States of the conversation flow."""

    STARTED = "started"
    COLLECTING_DATA = "collecting_data"
    ASKING_FOLLOWUP = "asking_followup"
    COMPLETED = "completed"
    ERROR = "error"


class ActivityType(str, Enum):
    """Types of activities the user can log."""

    FITNESS = "fitness"
    CRICKET_COACHING = "cricket_coaching"
    CRICKET_MATCH = "cricket_match"
    REST_DAY = "rest_day"


class Conversation(SQLModel, table=True):
    """Database model for conversation sessions."""

    __tablename__ = "conversations"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Session identification
    session_id: str = Field(index=True, unique=True, description="Unique session identifier")
    user_id: str = Field(index=True, description="User identifier")

    # Conversation metadata
    activity_type: ActivityType = Field(index=True, description="Type of activity being logged")
    state: ConversationState = Field(
        default=ConversationState.STARTED,
        description="Current conversation state",
    )

    # Final results
    total_turns: int = Field(default=0, description="Total number of conversation turns")
    completion_status: str = Field(default="incomplete", description="Completion status")

    # Quality metrics
    data_quality_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Quality of collected data",
    )
    conversation_efficiency: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Efficiency of conversation",
    )

    # Final collected data (JSON field)
    final_data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # Timing fields
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    total_duration_seconds: float | None = Field(
        default=None,
        description="Total conversation duration",
    )

    # Related activity entry ID (nullable to handle failures)
    related_entry_id: int | None = Field(
        default=None,
        description="ID of the created activity entry",
    )
    related_entry_type: str | None = Field(
        default=None,
        description="Type of the created activity entry",
    )

    # Standard timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )

    # Relationships
    turns: list["ConversationTurn"] = Relationship(back_populates="conversation")


class ConversationTurn(SQLModel, table=True):
    """Database model for individual conversation turns."""

    __tablename__ = "conversation_turns"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Reference to conversation
    conversation_id: int = Field(foreign_key="conversations.id", index=True)
    turn_number: int = Field(description="Turn number in the conversation (1-based)")

    # User input
    user_input: str = Field(description="User's voice transcript for this turn")
    transcript_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score from speech-to-text",
    )

    # AI response
    ai_response: str | None = Field(default=None, description="AI's response or follow-up question")
    follow_up_question: str | None = Field(
        default=None,
        description="Specific follow-up question asked",
    )
    target_field: str | None = Field(
        default=None,
        description="Field the question was trying to collect",
    )

    # Data extraction for this turn
    extracted_data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    extraction_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence in data extraction",
    )

    # Turn analysis
    data_completeness_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Data completeness after this turn",
    )
    missing_fields: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Timing
    turn_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    processing_duration: float | None = Field(default=None, description="Time to process this turn")

    # Standard timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )

    # Relationships
    conversation: Conversation = Relationship(back_populates="turns")


class ConversationAnalytics(SQLModel, table=True):
    """Analytics and insights about conversation patterns."""

    __tablename__ = "conversation_analytics"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Time period for analytics
    date: datetime = Field(index=True, description="Date for these analytics")
    user_id: str | None = Field(
        default=None,
        index=True,
        description="User ID (null for global analytics)",
    )

    # Conversation metrics
    total_conversations: int = Field(default=0)
    completed_conversations: int = Field(default=0)
    average_turns_per_conversation: float | None = Field(default=None)
    average_conversation_duration: float | None = Field(default=None)

    # Quality metrics
    average_data_quality: float | None = Field(default=None, ge=0.0, le=1.0)
    average_efficiency: float | None = Field(default=None, ge=0.0, le=1.0)

    # Activity breakdown
    activity_breakdown: dict[str, int] = Field(default_factory=dict, sa_column=Column(JSON))

    # Common patterns
    most_asked_questions: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    common_missing_fields: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Standard timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
