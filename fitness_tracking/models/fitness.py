"""Fitness tracking database models."""

from enum import Enum

from sqlmodel import Field

from database.models.base import (
    BaseTable,
    CommonEntryFields,
    EntryType,
    UserSessionMixin,
    VoiceProcessingMixin,
)


class FitnessType(str, Enum):
    """Types of fitness activities."""

    RUNNING = "running"
    GYM = "gym"
    CRICKET_SPECIFIC = "cricket_specific"
    STRENGTH_TRAINING = "strength_training"
    CARDIO = "cardio"
    OTHER = "other"


class Intensity(str, Enum):
    """Intensity levels for activities."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FitnessEntry(
    BaseTable,
    UserSessionMixin,
    VoiceProcessingMixin,
    CommonEntryFields,
    table=True,
):
    """Database model for fitness entries."""

    __tablename__ = "fitness_entries"

    # Set default entry type
    entry_type: EntryType = Field(
        default=EntryType.FITNESS,
        index=True,
        description="Type of entry",
    )

    # Fitness-specific fields
    fitness_type: FitnessType = Field(description="Type of fitness activity")
    duration_minutes: int = Field(gt=0, description="Duration in minutes")
    intensity: Intensity = Field(description="Intensity level")
    energy_level: int = Field(ge=1, le=5, description="Energy level from 1-5")
    details: str = Field(description="Additional details about the activity")

    # Optional tracking fields
    distance_km: float | None = Field(default=None, ge=0, description="Distance covered in km")
    calories_burned: int | None = Field(default=None, ge=0, description="Estimated calories burned")
    heart_rate_avg: int | None = Field(default=None, ge=0, description="Average heart rate")
    heart_rate_max: int | None = Field(default=None, ge=0, description="Maximum heart rate")

    # Weather and environment (for outdoor activities)
    weather_conditions: str | None = Field(default=None, description="Weather conditions")
    location: str | None = Field(default=None, description="Activity location")
