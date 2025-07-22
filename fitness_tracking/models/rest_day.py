from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy import Enum as SA_Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models.activity import ActivityEntry
from fitness_tracking.schemas.enums.activity_type import ActivityType

if TYPE_CHECKING:
    from voice_processing.models.conversation import Conversation


class RestDayEntry(ActivityEntry):
    """Model for rest day entries."""

    __tablename__ = "rest_day_entries"

    # Set the entry type
    activity_type: Mapped[ActivityType] = mapped_column(
        SA_Enum(ActivityType),
        default=ActivityType.REST_DAY,
        index=True,
    )

    # Rest day specifics
    rest_type: Mapped[str] = mapped_column(String)  # active, complete, partial
    planned: Mapped[bool] = mapped_column(default=False)

    # Recovery activities
    recovery_activities: Mapped[list[str] | None] = mapped_column(JSON)
    sleep_hours: Mapped[float | None] = mapped_column()
    sleep_quality: Mapped[int | None] = mapped_column()  # 1-10 scale

    # Physical state
    muscle_soreness: Mapped[int | None] = mapped_column()  # 1-10 scale
    fatigue_level: Mapped[int | None] = mapped_column()  # 1-10 scale
    stress_level: Mapped[int | None] = mapped_column()  # 1-10 scale

    # Recovery metrics
    recovery_score: Mapped[int | None] = mapped_column()  # 1-100 scale
    readiness_for_next_workout: Mapped[int | None] = mapped_column()  # 1-10 scale

    # Wellness activities
    meditation_minutes: Mapped[int | None] = mapped_column()
    stretching_minutes: Mapped[int | None] = mapped_column()
    massage_minutes: Mapped[int | None] = mapped_column()

    # Nutrition focus
    hydration_liters: Mapped[float | None] = mapped_column()
    protein_focus: Mapped[bool | None] = mapped_column()
    nutrition_notes: Mapped[str | None] = mapped_column(String)

    # relationship to conversation
    conversation: Mapped["Conversation"] = relationship(
        back_populates="activity_entries",
    )
