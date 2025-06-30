"""Conversation management schemas for multi-turn voice interactions."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import Field

from common.schemas import AppBaseModel


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


class ConversationContext(AppBaseModel):
    """Context information for a conversation session."""

    session_id: str
    user_id: str
    activity_type: ActivityType
    state: ConversationState = ConversationState.STARTED

    # Conversation data
    collected_data: dict[str, Any] = Field(default_factory=dict)
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    transcript_history: list[dict[str, Any]] = Field(
        default_factory=list, description="All transcripts with metadata"
    )

    # Tracking
    turn_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DataCompleteness(AppBaseModel):
    """Analysis of how complete the collected data is."""

    is_complete: bool
    completeness_score: float = Field(ge=0.0, le=1.0, description="0.0 to 1.0 completion score")
    missing_fields: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in data quality")

    # Optional suggestions
    next_question_priority: Literal["high", "medium", "low"] = "medium"
    suggested_question: str | None = None


class FollowUpQuestion(AppBaseModel):
    """A follow-up question to ask the user."""

    question: str
    field_target: str = Field(description="Which data field this question aims to collect")
    question_type: Literal["required", "optional", "clarification"] = "required"
    context: str | None = Field(default=None, description="Additional context for the question")

    # Question metadata
    priority: Literal["high", "medium", "low"] = "medium"
    max_attempts: int = 3
    current_attempts: int = 0


class ConversationAnalysis(AppBaseModel):
    """Analysis of the current conversation state and next steps."""

    data_completeness: DataCompleteness
    next_question: FollowUpQuestion | None = None
    should_continue: bool
    can_generate_final_output: bool

    # Analysis metadata
    analysis_confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(description="Explanation of the analysis decision")


class ConversationTurn(AppBaseModel):
    """A single turn in the conversation."""

    turn_number: int
    user_input: str
    system_response: str | None = None
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationResult(AppBaseModel):
    """Final result of a completed conversation."""

    session_id: str
    activity_type: ActivityType
    final_data: dict[str, Any]
    total_turns: int
    completion_status: Literal["completed", "incomplete", "error"]

    # Quality metrics
    data_quality_score: float = Field(ge=0.0, le=1.0)
    conversation_efficiency: float = Field(
        ge=0.0,
        le=1.0,
        description="How efficiently data was collected",
    )

    # Metadata
    started_at: datetime
    completed_at: datetime
    total_duration_seconds: float


class QuestionTemplate(AppBaseModel):
    """Template for generating contextual questions."""

    activity_type: ActivityType
    field_name: str
    question_variations: list[str]
    follow_up_prompts: list[str] = Field(default_factory=list)
    validation_hints: list[str] = Field(default_factory=list)


# Message types for WebSocket communication
class ConversationMessage(AppBaseModel):
    """Message for conversation updates via WebSocket."""

    type: Literal[
        "conversation_started",
        "follow_up_question",
        "data_extracted",
        "conversation_completed",
        "conversation_error",
    ]
    session_id: str
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
