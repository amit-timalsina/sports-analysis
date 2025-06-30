"""Schemas for conversation analytics and insights."""

from datetime import datetime
from typing import Any

from pydantic import Field

from common.schemas import AppBaseModel


class ConversationTurnResponse(AppBaseModel):
    """Response schema for conversation turn data."""

    turn_number: int
    user_input: str
    transcript_confidence: float
    ai_response: str | None = None
    follow_up_question: str | None = None
    target_field: str | None = None
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    turn_timestamp: datetime
    processing_duration: float | None = None


class ConversationDetailResponse(AppBaseModel):
    """Detailed conversation response with all turns."""

    conversation_id: int
    session_id: str
    user_id: str
    activity_type: str
    state: str
    total_turns: int
    completion_status: str
    data_quality_score: float | None = None
    conversation_efficiency: float | None = None
    final_data: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    completed_at: datetime | None = None
    total_duration_seconds: float | None = None

    # All conversation turns
    turns: list[ConversationTurnResponse] = Field(default_factory=list)


class ConversationAnalyticsResponse(AppBaseModel):
    """Analytics response for conversation metrics."""

    # Basic metrics
    total_conversations: int
    completed_conversations: int
    completion_rate: float

    # Quality metrics
    average_turns_per_conversation: float | None = None
    average_duration_seconds: float | None = None
    average_data_quality: float | None = None
    average_efficiency: float | None = None

    # Activity breakdown
    activity_breakdown: dict[str, int] = Field(default_factory=dict)


class QuestionEffectivenessResponse(AppBaseModel):
    """Response for question effectiveness analysis."""

    question: str
    target_field: str
    frequency: int
    success_rate: float | None = None
    average_user_response_length: float | None = None


class ConversationInsightsResponse(AppBaseModel):
    """Comprehensive conversation insights."""

    analytics: ConversationAnalyticsResponse
    most_asked_questions: list[QuestionEffectivenessResponse] = Field(default_factory=list)
    common_missing_fields: list[str] = Field(default_factory=list)

    # Trends
    quality_trend: list[dict[str, Any]] = Field(default_factory=list)
    efficiency_trend: list[dict[str, Any]] = Field(default_factory=list)
