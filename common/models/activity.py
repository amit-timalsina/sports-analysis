"""Shared SQLAlchemy 2.0 models used across features."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy import Enum as SA_Enum
from sqlalchemy.orm import Mapped, mapped_column

from common.schemas.entry_type import EntryType
from database.base import ProductionBase


class ActivityEntryBase(ProductionBase):
    """Enhanced base model for all activity entries with stronger conversation relationship."""

    __abstract__ = True

    # User and session identification
    user_id: Mapped[str] = mapped_column(String, index=True)
    session_id: Mapped[str] = mapped_column(String, index=True)

    # Conversation relationship (strengthened - required)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"),
        index=True,
    )

    # Entry type classification
    entry_type: Mapped[EntryType] = mapped_column(
        SA_Enum(EntryType),
        index=True,
    )

    # Voice processing metadata
    original_transcript: Mapped[str] = mapped_column(String)
    overall_confidence_score: Mapped[float] = mapped_column()
    processing_duration: Mapped[float | None] = mapped_column()

    # Data quality tracking
    data_quality_score: Mapped[float | None] = mapped_column()
    manual_overrides: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    validation_notes: Mapped[str | None] = mapped_column(String)

    # Common activity fields
    mental_state: Mapped[str] = mapped_column(String)
    energy_level: Mapped[int | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(String)

    # Timing
    activity_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
