"""Fitness activity Pydantic schemas for API contracts."""

from datetime import time
from typing import Any, Literal

from pydantic import Field

from common.schemas import AppBaseModel, PrimaryKeyBase, TimestampBase
from common.schemas.activity import ActivityEntryBase
from common.schemas.entry_type import EntryType
from fitness_tracking.schemas.exercise_type import ExerciseType
from fitness_tracking.schemas.intensity_level import IntensityLevel

# === Data Extraction Schemas for OpenAI ===


class FitnessDataExtraction(AppBaseModel):
    """Schema for structured fitness data extraction from voice input."""

    fitness_type: (
        Literal[
            "running",
            "strength_training",
            "cricket_specific",
            "cardio",
            "flexibility",
            "general_fitness",
        ]
        | None
    ) = Field(None, description="Type of fitness activity")
    duration_minutes: int | None = Field(None, ge=1, le=480, description="Duration in minutes")
    intensity: Literal["low", "medium", "high"] | None = Field(
        None,
        description="Exercise intensity",
    )
    details: str | None = Field(None, description="Additional details about the activity")
    mental_state: str | None = Field(None, description="Mental state during exercise")
    energy_level: int | None = Field(None, ge=1, le=10, description="Energy level 1-10")
    distance_km: float | None = Field(None, ge=0, description="Distance covered in kilometers")
    calories_burned: int | None = Field(None, ge=1, description="Estimated calories burned")
    location: str | None = Field(None, description="Location where activity was performed")


# === Main Fitness Schemas ===


class FitnessEntryBase(ActivityEntryBase):
    """Base schema for fitness entries."""

    entry_type: EntryType = Field(default=EntryType.FITNESS, description="Entry type")
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

    # Data quality tracking
    processing_duration: float | None = Field(None, ge=0.0, description="Processing duration")
    data_quality_score: float | None = Field(None, ge=0.0, le=1.0, description="Data quality score")
    manual_overrides: dict[str, Any] | None = Field(None, description="Manual data overrides")
    validation_notes: str | None = Field(None, description="Validation notes")
    energy_level: int | None = Field(None, ge=1, le=10, description="Energy level 1-10")
    notes: str | None = Field(None, description="Additional notes")


class FitnessEntryUpdate(AppBaseModel):
    """Schema for updating a fitness entry."""

    exercise_type: ExerciseType | None = None
    exercise_name: str | None = None
    duration_minutes: int | None = Field(None, gt=0)
    intensity: IntensityLevel | None = None
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
    data_quality_score: float | None = Field(None, ge=0.0, le=1.0)
    manual_overrides: dict[str, Any] | None = None
    validation_notes: str | None = None
    energy_level: int | None = Field(None, ge=1, le=10)
    notes: str | None = None


class FitnessEntryRead(PrimaryKeyBase, TimestampBase, FitnessEntryBase):
    """Schema for reading fitness entry data."""

    calories_burned: int | None
    distance_km: float | None
    sets: int | None
    reps: int | None
    weight_kg: float | None
    heart_rate_avg: int | None
    heart_rate_max: int | None
    workout_rating: int | None
    equipment_used: list[str] | None
    location: str | None
    gym_name: str | None
    weather_conditions: str | None
    temperature: float | None
    workout_partner: str | None
    trainer_name: str | None
    start_time: time | None
    end_time: time | None
    processing_duration: float | None
    data_quality_score: float | None
    manual_overrides: dict[str, Any] | None
    validation_notes: str | None
    energy_level: int | None
    notes: str | None


# === Rest Day Entry Schemas ===


class RestDayDataExtraction(AppBaseModel):
    """Schema for structured rest day data extraction from voice input."""

    rest_type: Literal["active_recovery", "complete_rest", "light_activity"] | None = Field(
        None,
        description="Type of rest day",
    )
    physical_state: str | None = Field(None, description="Physical state description")
    fatigue_level: int | None = Field(None, ge=1, le=10, description="Fatigue level 1-10")
    energy_level: int | None = Field(None, ge=1, le=10, description="Energy level 1-10")
    mental_state: str | None = Field(None, description="Mental state description")
    recovery_activities: list[str] | None = Field(None, description="Recovery activities performed")
    notes: str | None = Field(None, description="Additional notes")


class RestDayEntryBase(ActivityEntryBase):
    """Base schema for rest day entries."""

    entry_type: EntryType = Field(default=EntryType.REST_DAY, description="Entry type")
    rest_type: str = Field(..., description="Type of rest (active, complete, partial)")
    planned: bool = Field(default=False, description="Whether this was a planned rest day")


class RestDayEntryCreate(RestDayEntryBase):
    """Schema for creating a rest day entry."""

    # Recovery activities
    recovery_activities: list[str] | None = Field(None, description="Recovery activities performed")
    sleep_hours: float | None = Field(None, ge=0.0, le=24.0, description="Hours of sleep")
    sleep_quality: int | None = Field(None, ge=1, le=10, description="Sleep quality 1-10")

    # Physical state
    muscle_soreness: int | None = Field(None, ge=1, le=10, description="Muscle soreness level 1-10")
    fatigue_level: int | None = Field(None, ge=1, le=10, description="Fatigue level 1-10")
    stress_level: int | None = Field(None, ge=1, le=10, description="Stress level 1-10")

    # Recovery metrics
    recovery_score: int | None = Field(None, ge=1, le=100, description="Recovery score 1-100")
    readiness_for_next_workout: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Readiness for next workout 1-10",
    )

    # Wellness activities
    meditation_minutes: int | None = Field(None, ge=0, description="Meditation time in minutes")
    stretching_minutes: int | None = Field(None, ge=0, description="Stretching time in minutes")
    massage_minutes: int | None = Field(None, ge=0, description="Massage time in minutes")

    # Nutrition focus
    hydration_liters: float | None = Field(None, ge=0.0, description="Water intake in liters")
    protein_focus: bool | None = Field(None, description="Whether focused on protein intake")
    nutrition_notes: str | None = Field(None, description="Nutrition notes")

    # Data quality tracking
    processing_duration: float | None = Field(None, ge=0.0, description="Processing duration")
    data_quality_score: float | None = Field(None, ge=0.0, le=1.0, description="Data quality score")
    manual_overrides: dict[str, Any] | None = Field(None, description="Manual data overrides")
    validation_notes: str | None = Field(None, description="Validation notes")
    energy_level: int | None = Field(None, ge=1, le=10, description="Energy level 1-10")
    notes: str | None = Field(None, description="Additional notes")


class RestDayEntryUpdate(AppBaseModel):
    """Schema for updating a rest day entry."""

    rest_type: str | None = None
    planned: bool | None = None
    recovery_activities: list[str] | None = None
    sleep_hours: float | None = Field(None, ge=0.0, le=24.0)
    sleep_quality: int | None = Field(None, ge=1, le=10)
    muscle_soreness: int | None = Field(None, ge=1, le=10)
    fatigue_level: int | None = Field(None, ge=1, le=10)
    stress_level: int | None = Field(None, ge=1, le=10)
    recovery_score: int | None = Field(None, ge=1, le=100)
    readiness_for_next_workout: int | None = Field(None, ge=1, le=10)
    meditation_minutes: int | None = Field(None, ge=0)
    stretching_minutes: int | None = Field(None, ge=0)
    massage_minutes: int | None = Field(None, ge=0)
    hydration_liters: float | None = Field(None, ge=0.0)
    protein_focus: bool | None = None
    nutrition_notes: str | None = None
    data_quality_score: float | None = Field(None, ge=0.0, le=1.0)
    manual_overrides: dict[str, Any] | None = None
    validation_notes: str | None = None
    energy_level: int | None = Field(None, ge=1, le=10)
    notes: str | None = None


class RestDayEntryRead(PrimaryKeyBase, TimestampBase, RestDayEntryBase):
    """Schema for reading rest day entry data."""

    recovery_activities: list[str] | None
    sleep_hours: float | None
    sleep_quality: int | None
    muscle_soreness: int | None
    fatigue_level: int | None
    stress_level: int | None
    recovery_score: int | None
    readiness_for_next_workout: int | None
    meditation_minutes: int | None
    stretching_minutes: int | None
    massage_minutes: int | None
    hydration_liters: float | None
    protein_focus: bool | None
    nutrition_notes: str | None
    processing_duration: float | None
    data_quality_score: float | None
    manual_overrides: dict[str, Any] | None
    validation_notes: str | None
    energy_level: int | None
    notes: str | None
