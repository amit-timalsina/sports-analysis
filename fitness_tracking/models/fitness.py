"""Fitness tracking SQLAlchemy 2.0 models."""

from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy import Enum as SA_Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.mixins.relationship_factories import user_relationship_factory
from common.models.activity import ActivityEntry
from fitness_tracking.schemas.enums.activity_type import ActivityType
from fitness_tracking.schemas.enums.exercise_type import ExerciseType
from fitness_tracking.schemas.enums.intensity_level import IntensityLevel

if TYPE_CHECKING:
    from voice_processing.models.conversation import Conversation


class FitnessEntry(
    ActivityEntry,
    user_relationship_factory(  # type: ignore[misc]
        back_populates="fitness_entries",
        ondelete="SET NULL",
        nullable=True,
    ),
):
    """Model for fitness activity entries."""

    __tablename__ = "fitness_entries"

    # Set the entry type
    activity_type: Mapped[ActivityType] = mapped_column(
        SA_Enum(ActivityType),
        default=ActivityType.FITNESS,
        index=True,
    )

    # Core fitness fields
    exercise_type: Mapped[ExerciseType] = mapped_column(SA_Enum(ExerciseType))
    exercise_name: Mapped[str] = mapped_column(String)
    duration_minutes: Mapped[int] = mapped_column()
    intensity: Mapped[IntensityLevel] = mapped_column(SA_Enum(IntensityLevel))

    # Optional metrics
    calories_burned: Mapped[int | None] = mapped_column()
    distance_km: Mapped[float | None] = mapped_column()
    sets: Mapped[int | None] = mapped_column()
    reps: Mapped[int | None] = mapped_column()
    weight_kg: Mapped[float | None] = mapped_column()

    # Advanced metrics
    heart_rate_avg: Mapped[int | None] = mapped_column()
    heart_rate_max: Mapped[int | None] = mapped_column()
    workout_rating: Mapped[int | None] = mapped_column()

    # Equipment and location
    equipment_used: Mapped[list[str] | None] = mapped_column(JSON)
    location: Mapped[str | None] = mapped_column(String)
    gym_name: Mapped[str | None] = mapped_column(String)

    # Weather conditions (for outdoor activities)
    weather_conditions: Mapped[str | None] = mapped_column(String)
    temperature: Mapped[float | None] = mapped_column()

    # Social aspects
    workout_partner: Mapped[str | None] = mapped_column(String)
    trainer_name: Mapped[str | None] = mapped_column(String)

    # Timing specifics
    start_time: Mapped[time | None] = mapped_column()
    end_time: Mapped[time | None] = mapped_column()
    # relationship to conversation
    conversation: Mapped["Conversation"] = relationship(
        back_populates="fitness_entries",
    )
