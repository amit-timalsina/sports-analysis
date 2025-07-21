from sqlalchemy import JSON, String
from sqlalchemy import Enum as SA_Enum
from sqlalchemy.orm import Mapped, mapped_column

from common.models.activity import ActivityEntryBase
from common.schemas.entry_type import EntryType


class RestDayEntry(ActivityEntryBase):
    """SQLAlchemy 2.0 model for rest day entries."""

    __tablename__ = "rest_day_entries"

    # Set the entry type
    entry_type: Mapped[EntryType] = mapped_column(
        SA_Enum(EntryType),
        default=EntryType.REST_DAY,
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
