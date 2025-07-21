"""Conversation Pydantic schemas for API contracts."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from common.schemas import AppBaseModel, PrimaryKeyBase, TimestampBase
from voice_processing.schemas.conversation_detail_enums import (
    ActivityType,
    ConversationStage,
    MessageType,
    QuestionType,
)
from voice_processing.schemas.conversation_enums import ConversationState, ResolutionStatus


class DataCompleteness(AppBaseModel):
    """Schema for data completeness analysis."""

    is_complete: bool = Field(..., description="Whether all required data is collected")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in completeness")
    missing_fields: list[str] = Field(
        default_factory=list,
        description="List of missing required fields",
    )
    collected_fields: list[str] = Field(
        default_factory=list,
        description="List of collected fields",
    )
    total_required_fields: int = Field(..., description="Total number of required fields")
    completeness_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage completion",
    )


class FollowUpQuestion(AppBaseModel):
    """Schema for follow-up questions."""

    question: str = Field(..., description="The question text")
    field_target: str = Field(..., description="Target field this question aims to collect")
    question_type: str = Field(..., description="Type of question (direct, clarification, etc.)")
    priority: int = Field(..., description="Question priority (1=highest)")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for the question",
    )


class ConversationAnalysis(AppBaseModel):
    """Schema for conversation analysis results."""

    data_completeness: DataCompleteness = Field(..., description="Data completeness analysis")
    next_question: FollowUpQuestion | None = Field(None, description="Next question to ask if any")
    should_continue: bool = Field(..., description="Whether conversation should continue")
    can_generate_final_output: bool = Field(
        ...,
        description="Whether final output can be generated",
    )
    analysis_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in analysis")
    reasoning: str = Field(..., description="Reasoning for the analysis decision")


class ConversationContext(AppBaseModel):
    """Schema for conversation context during processing."""

    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    activity_type: ActivityType = Field(..., description="Activity type")
    state: ConversationState = Field(default=ConversationState.STARTED, description="Current state")
    stage: ConversationStage = Field(
        default=ConversationStage.INITIAL_INPUT,
        description="Current stage",
    )
    turn_count: int = Field(default=0, description="Number of turns completed")
    collected_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Collected data so far",
    )
    transcript_history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="History of transcripts",
    )
    question_attempts: dict[str, int] = Field(
        default_factory=dict,
        description="Follow-up attempts per missing field",
    )


class ConversationResult(AppBaseModel):
    """Schema for final conversation results."""

    final_data: dict[str, Any] = Field(..., description="Final collected data")
    total_turns: int = Field(..., description="Total number of turns")
    data_quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall data quality score")
    conversation_efficiency: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Conversation efficiency score",
    )
    completion_status: str = Field(..., description="How the conversation was completed")
    session_id: str = Field(..., description="Session identifier")


# === Conversation Schemas ===


class ConversationBase(AppBaseModel):
    """Base schema for conversation data."""

    session_id: str = Field(..., description="Unique session identifier")
    activity_type: ActivityType = Field(..., description="Type of activity being logged")
    state: ConversationState = Field(
        default=ConversationState.STARTED,
        description="Current conversation state",
    )
    stage: ConversationStage = Field(
        default=ConversationStage.INITIAL_INPUT,
        description="Current stage in data collection",
    )
    max_turns_allowed: int = Field(default=8, description="Maximum allowed conversation turns")


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""

    current_data: dict[str, Any] = Field(default_factory=dict, description="Current collected data")
    data_confidence: dict[str, float] = Field(
        default_factory=dict,
        description="Confidence scores for data",
    )


class ConversationUpdate(AppBaseModel):
    """Schema for updating a conversation."""

    state: ConversationState | None = None
    stage: ConversationStage | None = None
    current_data: dict[str, Any] | None = None
    data_confidence: dict[str, float] | None = None
    missing_fields: list[str] | None = None
    validation_errors: dict[str, str] | None = None
    pending_questions: list[str] | None = None
    question_attempts: dict[str, int] | None = None
    total_turns: int | None = None
    total_messages: int | None = None
    completion_status: str | None = None
    overall_data_quality_score: float | None = Field(None, ge=0.0, le=1.0)
    conversation_efficiency: float | None = Field(None, ge=0.0, le=1.0)
    user_satisfaction_score: float | None = Field(None, ge=0.0, le=1.0)
    final_data: dict[str, Any] | None = None
    completed_at: datetime | None = None
    total_duration_seconds: float | None = None
    activity_entry_id: UUID | None = None
    activity_entry_type: str | None = None


class ConversationRead(PrimaryKeyBase, TimestampBase, ConversationBase):
    """Schema for reading conversation data."""

    current_data: dict[str, Any]
    data_confidence: dict[str, float]
    missing_fields: list[str]
    validation_errors: dict[str, str]
    pending_questions: list[str]
    question_attempts: dict[str, int]
    total_turns: int
    total_messages: int
    completion_status: str
    overall_data_quality_score: float | None = Field(None, ge=0.0, le=1.0)
    conversation_efficiency: float | None = Field(None, ge=0.0, le=1.0)
    user_satisfaction_score: float | None = Field(None, ge=0.0, le=1.0)
    final_data: dict[str, Any]
    started_at: datetime
    completed_at: datetime | None
    last_activity_at: datetime
    total_duration_seconds: float | None
    activity_entry_id: UUID | None
    activity_entry_type: str | None


# === Message Schemas ===


class ConversationMessageBase(AppBaseModel):
    """Base schema for conversation message data."""

    conversation_id: UUID = Field(..., description="ID of the parent conversation")
    message_type: MessageType = Field(..., description="Type of message")
    sequence_number: int = Field(..., description="Sequential number within conversation")
    content: str = Field(..., description="Message content")


class ConversationMessageCreate(ConversationMessageBase):
    """Schema for creating a conversation message."""

    turn_id: UUID | None = None
    parent_message_id: UUID | None = None
    raw_transcript: str | None = None
    transcript_confidence: float | None = Field(None, ge=0.0, le=1.0)
    processing_duration: float | None = None
    ai_model_used: str | None = None
    ai_temperature: float | None = None
    ai_tokens_used: int | None = None
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    extraction_confidence: float | None = Field(None, ge=0.0, le=1.0)


class ConversationMessageRead(PrimaryKeyBase, TimestampBase, ConversationMessageBase):
    """Schema for reading conversation message data."""

    turn_id: UUID | None
    parent_message_id: UUID | None
    raw_transcript: str | None
    transcript_confidence: float | None
    processing_duration: float | None
    ai_model_used: str | None
    ai_temperature: float | None
    ai_tokens_used: int | None
    extracted_data: dict[str, Any]
    extraction_confidence: float | None
    message_timestamp: datetime


# === Turn Schemas ===


class ConversationTurnBase(AppBaseModel):
    """Base schema for conversation turn data."""

    conversation_id: UUID = Field(..., description="ID of the parent conversation")
    turn_number: int = Field(..., description="Turn number in the conversation")


class ConversationTurnCreate(ConversationTurnBase):
    """Schema for creating a conversation turn."""

    data_extracted_this_turn: dict[str, Any] = Field(default_factory=dict)
    questions_resolved: list[str] = Field(default_factory=list)
    new_questions_raised: list[str] = Field(default_factory=list)
    turn_effectiveness_score: float | None = Field(None, ge=0.0, le=1.0)
    data_completeness_after_turn: float | None = Field(None, ge=0.0, le=1.0)
    turn_strategy: str | None = None


class ConversationTurnRead(PrimaryKeyBase, TimestampBase, ConversationTurnBase):
    """Schema for reading conversation turn data."""

    data_extracted_this_turn: dict[str, Any]
    questions_resolved: list[str]
    new_questions_raised: list[str]
    turn_effectiveness_score: float | None
    data_completeness_after_turn: float | None
    turn_strategy: str | None
    turn_started_at: datetime
    turn_completed_at: datetime | None
    turn_duration_seconds: float | None


# === Question Context Schemas ===


class QuestionContextBase(AppBaseModel):
    """Base schema for question context data."""

    conversation_id: UUID = Field(..., description="ID of the parent conversation")
    target_field: str = Field(..., description="Field this question aims to collect")
    question_text: str = Field(..., description="The actual question text")
    question_type: QuestionType = Field(..., description="Type of question")
    asked_at_turn: int = Field(..., description="Turn number when first asked")


class QuestionContextCreate(QuestionContextBase):
    """Schema for creating a question context."""

    attempts_count: int = Field(default=1)
    max_attempts: int = Field(default=3)
    resolution_status: ResolutionStatus = Field(default=ResolutionStatus.PENDING)
    question_strategy: str = Field(default="direct")
    context_data: dict[str, Any] = Field(default_factory=dict)


class QuestionContextUpdate(AppBaseModel):
    """Schema for updating a question context."""

    attempts_count: int | None = None
    resolution_status: ResolutionStatus | None = None
    resolved_at_turn: int | None = None
    resolved_with_confidence: float | None = Field(None, ge=0.0, le=1.0)
    final_answer: str | None = None
    resolved_at: datetime | None = None


class QuestionContextRead(PrimaryKeyBase, TimestampBase, QuestionContextBase):
    """Schema for reading question context data."""

    attempts_count: int
    max_attempts: int
    resolution_status: ResolutionStatus
    question_strategy: str
    context_data: dict[str, Any]
    resolved_at_turn: int | None
    resolved_with_confidence: float | None
    final_answer: str | None
    first_asked_at: datetime
    resolved_at: datetime | None


# === Analytics Schemas ===


class ConversationAnalyticsBase(AppBaseModel):
    """Base schema for conversation analytics data."""

    date: datetime = Field(..., description="Date for these analytics")
    user_id: str | None = Field(None, description="User ID (null for global analytics)")


class ConversationAnalyticsCreate(ConversationAnalyticsBase):
    """Schema for creating conversation analytics."""

    total_conversations: int = Field(default=0)
    completed_conversations: int = Field(default=0)
    abandoned_conversations: int = Field(default=0)
    error_conversations: int = Field(default=0)
    average_turns_per_conversation: float | None = None
    average_messages_per_conversation: float | None = None
    average_conversation_duration: float | None = None
    median_conversation_duration: float | None = None
    average_data_quality: float | None = Field(None, ge=0.0, le=1.0)
    average_efficiency: float | None = Field(None, ge=0.0, le=1.0)
    average_user_satisfaction: float | None = Field(None, ge=0.0, le=1.0)
    activity_breakdown: dict[str, int] = Field(default_factory=dict)
    completion_rate_by_activity: dict[str, float] = Field(default_factory=dict)
    most_asked_questions: list[dict[str, Any]] = Field(default_factory=list)
    most_problematic_fields: list[dict[str, Any]] = Field(default_factory=list)
    question_success_rates: dict[str, float] = Field(default_factory=dict)
    average_time_per_stage: dict[str, float] = Field(default_factory=dict)
    stage_completion_rates: dict[str, float] = Field(default_factory=dict)
    average_ai_response_time: float | None = None
    ai_model_usage: dict[str, int] = Field(default_factory=dict)
    total_ai_tokens_used: int | None = None


class ConversationAnalyticsUpdate(AppBaseModel):
    """Schema for updating conversation analytics."""

    total_conversations: int | None = None
    completed_conversations: int | None = None
    abandoned_conversations: int | None = None
    error_conversations: int | None = None
    average_turns_per_conversation: float | None = None
    average_messages_per_conversation: float | None = None
    average_conversation_duration: float | None = None
    median_conversation_duration: float | None = None
    average_data_quality: float | None = Field(None, ge=0.0, le=1.0)
    average_efficiency: float | None = Field(None, ge=0.0, le=1.0)
    average_user_satisfaction: float | None = Field(None, ge=0.0, le=1.0)
    activity_breakdown: dict[str, int] | None = None
    completion_rate_by_activity: dict[str, float] | None = None
    most_asked_questions: list[dict[str, Any]] | None = None
    most_problematic_fields: list[dict[str, Any]] | None = None
    question_success_rates: dict[str, float] | None = None
    average_time_per_stage: dict[str, float] | None = None
    stage_completion_rates: dict[str, float] | None = None
    average_ai_response_time: float | None = None
    ai_model_usage: dict[str, int] | None = None
    total_ai_tokens_used: int | None = None


class ConversationAnalyticsRead(PrimaryKeyBase, TimestampBase, ConversationAnalyticsBase):
    """Schema for reading conversation analytics data."""

    total_conversations: int
    completed_conversations: int
    abandoned_conversations: int
    error_conversations: int
    average_turns_per_conversation: float | None
    average_messages_per_conversation: float | None
    average_conversation_duration: float | None
    median_conversation_duration: float | None
    average_data_quality: float | None
    average_efficiency: float | None
    average_user_satisfaction: float | None
    activity_breakdown: dict[str, int]
    completion_rate_by_activity: dict[str, float]
    most_asked_questions: list[dict[str, Any]]
    most_problematic_fields: list[dict[str, Any]]
    question_success_rates: dict[str, float]
    average_time_per_stage: dict[str, float]
    stage_completion_rates: dict[str, float]
    average_ai_response_time: float | None
    ai_model_usage: dict[str, int]
    total_ai_tokens_used: int | None
