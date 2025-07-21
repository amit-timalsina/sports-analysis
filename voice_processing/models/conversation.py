"""Voice processing SQLAlchemy 2.0 models for conversation management."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy import UUID as SA_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auth.models.user import User
from database.base import ProductionBase
from voice_processing.schemas.conversation_detail_enums import (
    ActivityType,
    ConversationStage,
    MessageType,
    QuestionType,
)
from voice_processing.schemas.conversation_enums import ConversationState, ResolutionStatus


class Conversation(ProductionBase):
    """Enhanced conversation model with better state management."""

    __tablename__ = "conversations"

    # Session identification
    session_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    # Conversation metadata
    activity_type: Mapped[ActivityType] = mapped_column(index=True)
    state: Mapped[ConversationState] = mapped_column(default=ConversationState.STARTED)
    stage: Mapped[ConversationStage] = mapped_column(default=ConversationStage.INITIAL_INPUT)

    # Enhanced state tracking
    current_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    data_confidence: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    missing_fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    validation_errors: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)

    # Conversation flow management
    pending_questions: Mapped[list[str]] = mapped_column(JSON, default=list)
    question_attempts: Mapped[dict[str, int]] = mapped_column(JSON, default=dict)
    max_turns_allowed: Mapped[int] = mapped_column(default=8)

    # Final results
    total_turns: Mapped[int] = mapped_column(default=0)
    total_messages: Mapped[int] = mapped_column(default=0)
    completion_status: Mapped[str] = mapped_column(String, default="incomplete")

    # Quality metrics
    overall_data_quality_score: Mapped[float | None] = mapped_column()
    conversation_efficiency: Mapped[float | None] = mapped_column()
    user_satisfaction_score: Mapped[float | None] = mapped_column()

    # Final collected data
    final_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Custom timing fields
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    total_duration_seconds: Mapped[float | None] = mapped_column()

    # Activity relationship
    activity_entry_id: Mapped[UUID | None] = mapped_column(SA_UUID, nullable=True)
    activity_entry_type: Mapped[str | None] = mapped_column(String)

    # Relationships
    turns: Mapped[list["ConversationTurn"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    question_contexts: Mapped[list["QuestionContext"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class ConversationTurn(ProductionBase):
    """Enhanced conversation turns with better message relationship."""

    __tablename__ = "conversation_turns"

    # Reference to conversation
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"), index=True)
    turn_number: Mapped[int] = mapped_column()

    # Turn-level analysis
    data_extracted_this_turn: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    questions_resolved: Mapped[list[str]] = mapped_column(JSON, default=list)
    new_questions_raised: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Turn quality metrics
    turn_effectiveness_score: Mapped[float | None] = mapped_column()
    data_completeness_after_turn: Mapped[float | None] = mapped_column()

    # Turn strategy
    turn_strategy: Mapped[str | None] = mapped_column(String)

    # Custom timing fields for turns
    turn_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    turn_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    turn_duration_seconds: Mapped[float | None] = mapped_column()

    # Relationships
    conversation: Mapped[Conversation] = relationship(back_populates="turns")
    messages: Mapped[list["ConversationMessage"]] = relationship(back_populates="turn")


class ConversationMessage(ProductionBase):
    """Individual messages within a conversation with threading support."""

    __tablename__ = "conversation_messages"

    # References
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"), index=True)
    turn_id: Mapped[UUID | None] = mapped_column(ForeignKey("conversation_turns.id"), index=True)

    # Message identification
    message_type: Mapped[MessageType] = mapped_column()
    sequence_number: Mapped[int] = mapped_column()
    parent_message_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("conversation_messages.id"),
    )

    # Message content
    content: Mapped[str] = mapped_column(String)
    raw_transcript: Mapped[str | None] = mapped_column(String)

    # Processing metadata
    transcript_confidence: Mapped[float | None] = mapped_column()
    processing_duration: Mapped[float | None] = mapped_column()

    # AI-specific fields
    ai_model_used: Mapped[str | None] = mapped_column(String)
    ai_temperature: Mapped[float | None] = mapped_column()
    ai_tokens_used: Mapped[int | None] = mapped_column()

    # Data extraction for this message
    extracted_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    extraction_confidence: Mapped[float | None] = mapped_column()

    # Custom message timestamp
    message_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships
    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    turn: Mapped[ConversationTurn | None] = relationship(back_populates="messages")
    child_messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="parent_message",
        remote_side="ConversationMessage.id",
    )
    parent_message: Mapped["ConversationMessage | None"] = relationship(
        back_populates="child_messages",
        remote_side="ConversationMessage.parent_message_id",
    )


class QuestionContext(ProductionBase):
    """Context-aware question management system."""

    __tablename__ = "question_contexts"

    # References
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"), index=True)

    # Question identification
    target_field: Mapped[str] = mapped_column(String, index=True)
    question_text: Mapped[str] = mapped_column(String)
    question_type: Mapped[QuestionType] = mapped_column()

    # Question context
    asked_at_turn: Mapped[int] = mapped_column()
    attempts_count: Mapped[int] = mapped_column(default=1)
    max_attempts: Mapped[int] = mapped_column(default=3)
    resolution_status: Mapped[ResolutionStatus] = mapped_column(default=ResolutionStatus.PENDING)

    # Question strategy
    question_strategy: Mapped[str] = mapped_column(String, default="direct")
    context_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Success tracking
    resolved_at_turn: Mapped[int | None] = mapped_column()
    resolved_with_confidence: Mapped[float | None] = mapped_column()
    final_answer: Mapped[str | None] = mapped_column(String)

    # Custom timing fields for questions
    first_asked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    conversation: Mapped[Conversation] = relationship(back_populates="question_contexts")


class ConversationAnalytics(ProductionBase):
    """Enhanced analytics with more detailed insights."""

    __tablename__ = "conversation_analytics"

    # Time period for analytics
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    # Basic conversation metrics
    total_conversations: Mapped[int] = mapped_column(default=0)
    completed_conversations: Mapped[int] = mapped_column(default=0)
    abandoned_conversations: Mapped[int] = mapped_column(default=0)
    error_conversations: Mapped[int] = mapped_column(default=0)

    # Efficiency metrics
    average_turns_per_conversation: Mapped[float | None] = mapped_column()
    average_messages_per_conversation: Mapped[float | None] = mapped_column()
    average_conversation_duration: Mapped[float | None] = mapped_column()
    median_conversation_duration: Mapped[float | None] = mapped_column()

    # Quality metrics
    average_data_quality: Mapped[float | None] = mapped_column()
    average_efficiency: Mapped[float | None] = mapped_column()
    average_user_satisfaction: Mapped[float | None] = mapped_column()

    # Activity breakdown
    activity_breakdown: Mapped[dict[str, int]] = mapped_column(JSON, default=dict)
    completion_rate_by_activity: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)

    # Question analytics
    most_asked_questions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    most_problematic_fields: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    question_success_rates: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)

    # Stage analytics
    average_time_per_stage: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    stage_completion_rates: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)

    # AI performance metrics
    average_ai_response_time: Mapped[float | None] = mapped_column()
    ai_model_usage: Mapped[dict[str, int]] = mapped_column(JSON, default=dict)
    total_ai_tokens_used: Mapped[int | None] = mapped_column()


# Database indexes for performance
# Note: Complex indexes will be created via migration files due to SQLModel/SQLAlchemy limitations
