"""Fitness activity Pydantic schemas for API contracts."""

from datetime import time
from uuid import UUID

from pydantic import Field, model_validator

from common.schemas import AppBaseModel, PrimaryKeyBase, TimestampBase
from common.schemas.activity import ActivityEntryBase
from fitness_tracking.schemas.enums import ExerciseType, IntensityLevel
from fitness_tracking.schemas.enums.activity_type import ActivityType


class FitnessEntryBase(ActivityEntryBase):
    """Base schema for fitness entries."""

    activity_type: ActivityType = Field(default=ActivityType.FITNESS, description="Activity type")
    exercise_type: ExerciseType = Field(..., description="Type of exercise")
    exercise_name: str = Field(..., description="Name of the exercise")
    duration_minutes: int = Field(..., gt=0, description="Duration in minutes")
    intensity: IntensityLevel = Field(..., description="Intensity level")


class FitnessEntryCreate(FitnessEntryBase):
    """Schema for creating a fitness entry."""

    # Optional metrics
    calories_burned: int | None = Field(None, ge=0, description="Calories burned")
    distance_km: float | None = Field(None, ge=0.0, description="Distance in kilometers")
    sets: int | None = Field(None, ge=0, description="Number of sets")
    reps: int | None = Field(None, ge=0, description="Number of repetitions")
    weight_kg: float | None = Field(None, ge=0.0, description="Weight used in kg")

    # Advanced metrics
    heart_rate_avg: int | None = Field(None, ge=40, le=220, description="Average heart rate")
    heart_rate_max: int | None = Field(None, ge=40, le=220, description="Maximum heart rate")
    workout_rating: int | None = Field(None, ge=1, le=10, description="Workout rating 1-10")

    # Equipment and location
    equipment_used: list[str] | None = Field(None, description="Equipment used")
    location: str | None = Field(None, description="Workout location")
    gym_name: str | None = Field(None, description="Gym name")

    # Weather conditions (for outdoor activities)
    weather_conditions: str | None = Field(None, description="Weather conditions")
    temperature: float | None = Field(None, description="Temperature")

    # Social aspects
    workout_partner: str | None = Field(None, description="Workout partner")
    trainer_name: str | None = Field(None, description="Trainer name")

    # Timing specifics
    start_time: time | None = Field(None, description="Start time")
    end_time: time | None = Field(None, description="End time")

    @model_validator(mode="after")
    def validate_heart_rates(self) -> "FitnessEntryCreate":
        """Validate that max heart rate is greater than average heart rate."""
        if (
            self.heart_rate_avg is not None
            and self.heart_rate_max is not None
            and self.heart_rate_max < self.heart_rate_avg
        ):
            msg = "Maximum heart rate cannot be less than average heart rate"
            raise ValueError(msg)
        return self


class FitnessEntryUpdate(AppBaseModel):
    """Schema for updating a fitness entry."""

    exercise_type: ExerciseType | None = None
    exercise_name: str | None = None
    duration_minutes: int | None = Field(None, gt=0)
    intensity: IntensityLevel | None = None
    mental_state: str | None = None
    energy_level: int | None = Field(None, ge=1, le=10)
    notes: str | None = None
    calories_burned: int | None = Field(None, ge=0)
    distance_km: float | None = Field(None, ge=0.0)
    sets: int | None = Field(None, ge=0)
    reps: int | None = Field(None, ge=0)
    weight_kg: float | None = Field(None, ge=0.0)
    heart_rate_avg: int | None = Field(None, ge=40, le=220)
    heart_rate_max: int | None = Field(None, ge=40, le=220)
    workout_rating: int | None = Field(None, ge=1, le=10)
    equipment_used: list[str] | None = None
    location: str | None = None
    gym_name: str | None = None
    weather_conditions: str | None = None
    temperature: float | None = None
    workout_partner: str | None = None
    trainer_name: str | None = None
    start_time: time | None = None
    end_time: time | None = None

    @model_validator(mode="after")
    def validate_heart_rates(self) -> "FitnessEntryUpdate":
        """Validate that max heart rate is greater than average heart rate."""
        if (
            self.heart_rate_avg is not None
            and self.heart_rate_max is not None
            and self.heart_rate_max < self.heart_rate_avg
        ):
            msg = "Maximum heart rate cannot be less than average heart rate"
            raise ValueError(msg)
        return self


class FitnessEntryRead(PrimaryKeyBase, TimestampBase, FitnessEntryCreate):
    """Schema for reading fitness entry data."""


class FitnessEntryResponse(AppBaseModel):
    """Schema for fitness entry API responses with transcription data."""

    entries: list[FitnessEntryRead]
    count: int
    user_id: UUID
    days_back: int | None = None
    transcriptions: list[list[str]] | None = None
