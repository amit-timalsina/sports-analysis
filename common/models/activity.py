"""Shared SQLAlchemy 2.0 models used across features."""

from sqlalchemy import UUID, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import ProductionBase
from fitness_tracking.schemas.enums.activity_type import ActivityType


class ActivityEntry(
    ProductionBase,
):
    """Enhanced base model for all activity entries with stronger conversation relationship."""

    __abstract__ = True

    # Conversation relationship (strengthened - required)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id"),
        index=True,
    )

    # Activity type classification
    activity_type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType),
        index=True,
    )

    # Common activity fields
    mental_state: Mapped[str] = mapped_column(String)
    energy_level: Mapped[int | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(String)
