"""Voice processing Pydantic schemas."""

import re
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator

from common.config.settings import settings
from common.schemas import AppBaseModel


class TranscriptionResponse(AppBaseModel):
    """Response model for audio transcription."""

    text: str = Field(..., description="Transcribed text from audio")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score of transcription")
    language: str = Field(default="en", description="Detected or specified language")


class VoiceInputRequest(AppBaseModel):
    """Schema for voice input requests."""

    session_id: str = Field(..., min_length=1, max_length=100)
    audio_format: Literal["wav", "mp3", "webm", "m4a"] = "wav"
    sample_rate: int = Field(
        settings.audio.default_sample_rate,
        ge=settings.audio.min_sample_rate,
        le=settings.audio.max_sample_rate,
    )

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            msg = "Session ID must contain only alphanumeric characters, hyphens, and underscores"
            raise ValueError(
                msg,
            )
        return v


class ProcessedEntry(AppBaseModel):
    """Schema for processed voice entry responses."""

    entry_id: int | None = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: int = Field(..., ge=0)
    needs_clarification: bool = False
    clarification_questions: list[str] | None = None
    raw_transcript: str | None = None
    extracted_data: dict[str, Any] | None = None

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence_score(cls, v: float) -> float:
        """Round confidence score to 3 decimal places."""
        return round(v, 3)


class WebSocketMessage(AppBaseModel):
    """Schema for WebSocket messages."""

    type: str = Field(description="Message type")
    session_id: UUID = Field(description="Session identifier")
    data: dict[str, Any] | None = Field(default=None, description="Message data")
    error: str | None = Field(default=None, description="Error message if any")
    message: str | None = Field(default=None, description="Human readable message")


class SessionState(AppBaseModel):
    """Schema for tracking WebSocket session state."""

    session_id: str
    current_step: Literal["waiting", "recording", "processing", "confirming"] | None = "waiting"
    entry_type: Literal["fitness", "cricket_coaching", "cricket_match", "rest_day"] | None = None
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
    temp_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(UTC))


class VoiceProcessingResult(AppBaseModel):
    """Schema for complete voice processing results."""

    session_id: str
    transcript: str
    confidence: float
    entry_type: str
    structured_data: dict[str, Any]
    audio_saved: bool
    database_saved: bool
    processing_duration: float
    errors: list[str] = Field(default_factory=list)


class VoiceProcessingRequest(AppBaseModel):
    """Request schema for voice processing with explicit entry type."""

    entry_type: Literal["fitness", "cricket_coaching", "cricket_match", "rest_day"] = Field(
        description="Type of entry the user wants to create",
    )
    session_id: str = Field(description="Voice session identifier")
    user_id: str = Field(description="User identifier")


class VoiceDataMessage(AppBaseModel):
    """Schema for voice data WebSocket messages from client."""

    type: Literal["voice_data"] = Field(description="Message type")
    entry_type: Literal["fitness", "cricket_coaching", "cricket_match", "rest_day"] = Field(
        description="Type of entry to create",
    )
    session_id: str = Field(description="Session identifier")
    user_id: str = Field(default="demo_user", description="User identifier")
    # Audio data will be sent separately as bytes
