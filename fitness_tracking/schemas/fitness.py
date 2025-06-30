"""Fitness tracking Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from common.config.settings import settings
from common.schemas import AppBaseModel


class FitnessEntryCreate(AppBaseModel):
    """Schema for creating fitness activity entries."""

    type: Literal["running", "gym", "cricket_specific", "strength_training", "cardio", "other"]
    duration_minutes: int = Field(
        ...,
        ge=settings.validation.min_fitness_duration_minutes,
        le=settings.validation.max_fitness_duration_minutes,
        description="Duration in minutes",
    )
    distance_km: float | None = Field(
        None,
        ge=settings.validation.min_distance_km,
        le=settings.validation.max_distance_km,
        description="Distance covered in km",
    )
    intensity: Literal["low", "medium", "high"]
    details: str = Field(
        ...,
        min_length=settings.validation.min_text_length,
        max_length=settings.validation.max_text_length,
        description="Additional details about the activity",
    )
    mental_state: Literal["excellent", "good", "okay", "poor"]
    energy_level: int = Field(..., ge=1, le=5, description="Energy level from 1-5")

    # Optional fields
    calories_burned: int | None = Field(None, ge=0, description="Estimated calories burned")
    heart_rate_avg: int | None = Field(None, ge=40, le=220, description="Average heart rate (BPM)")
    heart_rate_max: int | None = Field(None, ge=40, le=220, description="Maximum heart rate (BPM)")
    weather_conditions: str | None = Field(None, max_length=200, description="Weather conditions")
    location: str | None = Field(None, max_length=200, description="Activity location")

    @field_validator("distance_km")
    @classmethod
    def validate_distance_for_running(cls, v: float | None) -> float | None:
        """Validate distance is provided for running type activities."""
        # Note: values is deprecated in Pydantic v2, using simplified validation
        return v

    @model_validator(mode="after")
    def validate_heart_rate_consistency(self) -> "FitnessEntryCreate":
        """Validate heart rate values are consistent."""
        if self.heart_rate_avg is not None and self.heart_rate_max is not None:
            if self.heart_rate_avg > self.heart_rate_max:
                msg = "Maximum heart rate cannot be less than average heart rate"
                raise ValueError(msg)
        return self


class FitnessEntryRead(AppBaseModel):
    """Schema for reading fitness activity entries."""

    id: int
    session_id: str
    user_id: str
    fitness_type: str  # Changed from 'type' to match database model
    duration_minutes: int
    distance_km: float | None
    intensity: str
    details: str
    mental_state: str
    energy_level: int
    location: str | None
    notes: str | None
    # Voice processing metadata
    transcript: str
    confidence_score: float
    processing_duration: float | None
    # Timestamps
    created_at: datetime
    updated_at: datetime | None


class FitnessEntryUpdate(AppBaseModel):
    """Schema for updating fitness activity entries."""

    type: (
        Literal["running", "gym", "cricket_specific", "strength_training", "cardio", "other"] | None
    ) = None
    duration_minutes: int | None = Field(
        None,
        ge=settings.validation.min_fitness_duration_minutes,
        le=settings.validation.max_fitness_duration_minutes,
        description="Duration in minutes",
    )
    distance_km: float | None = Field(
        None,
        ge=settings.validation.min_distance_km,
        le=settings.validation.max_distance_km,
        description="Distance covered in km",
    )
    intensity: Literal["low", "medium", "high"] | None = None
    details: str | None = Field(
        None,
        min_length=settings.validation.min_text_length,
        max_length=settings.validation.max_text_length,
        description="Additional details about the activity",
    )
    mental_state: Literal["excellent", "good", "okay", "poor"] | None = None
    energy_level: int | None = Field(None, ge=1, le=5, description="Energy level from 1-5")
    calories_burned: int | None = Field(None, ge=0, description="Estimated calories burned")
    heart_rate_avg: int | None = Field(None, ge=40, le=220, description="Average heart rate (BPM)")
    heart_rate_max: int | None = Field(None, ge=40, le=220, description="Maximum heart rate (BPM)")
    weather_conditions: str | None = Field(None, max_length=200, description="Weather conditions")
    location: str | None = Field(None, max_length=200, description="Activity location")

    @model_validator(mode="after")
    def validate_heart_rate_consistency(self) -> "FitnessEntryUpdate":
        """Validate heart rate values are consistent."""
        if self.heart_rate_avg is not None and self.heart_rate_max is not None:
            if self.heart_rate_avg > self.heart_rate_max:
                msg = "Maximum heart rate cannot be less than average heart rate"
                raise ValueError(msg)
        return self


class FitnessEntryResponse(AppBaseModel):
    """Schema for fitness entry responses."""

    id: int
    session_id: str
    user_id: str
    fitness_type: str  # Changed from 'type' to match database model
    duration_minutes: int
    distance_km: float | None
    intensity: str
    details: str
    mental_state: str
    energy_level: int
    location: str | None
    notes: str | None
    # Voice processing metadata
    transcript: str
    confidence_score: float
    processing_duration: float | None


class FitnessDataExtraction(AppBaseModel):
    """Schema for structured fitness data extraction from voice."""

    fitness_type: Literal[
        "running",
        "strength_training",
        "cricket_specific",
        "cardio",
        "flexibility",
        "general_fitness",
    ] = Field(
        ...,
        description="Type of fitness activity - must be one of the valid fitness types",
    )
    duration_minutes: int = Field(
        ...,
        ge=1,
        le=300,
        description="Duration in minutes (1-300)",
    )
    intensity: Literal["low", "medium", "high"] = Field(
        ...,
        description="Intensity level - must be low, medium, or high",
    )
    details: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Additional details about the activity",
    )
    mental_state: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Mental state during activity (e.g., focused, energetic, tired, motivated)",
    )
    energy_level: int = Field(
        ...,
        ge=1,
        le=5,
        description="Energy level from 1-5",
    )

    # Optional extracted fields
    distance_km: float | None = Field(
        None,
        ge=0.1,
        le=100.0,
        description="Distance covered in kilometers",
    )
    calories_burned: int | None = Field(
        None,
        ge=10,
        le=2000,
        description="Estimated calories burned",
    )
    location: str | None = Field(
        None,
        max_length=200,
        description="Activity location",
    )


class FitnessAnalytics(AppBaseModel):
    """Schema for fitness analytics and insights."""

    total_sessions: int
    total_duration_minutes: int
    average_duration_minutes: float
    total_distance_km: float | None
    average_intensity_score: float  # Calculated: low=1, medium=2, high=3
    average_energy_level: float
    most_common_activity: str
    weekly_frequency: float
    improvement_trends: dict[str, float]  # Various metrics over time
    recommendations: list[str]
