from typing import Any

from pydantic import Field

from common.schemas import AppBaseModel, TimestampBase
from common.schemas.activity import ActivityEntryBase
from common.schemas.primary_key_base import PrimaryKeyBase
from fitness_tracking.schemas.enums.activity_type import ActivityType


class RestDayEntryBase(ActivityEntryBase):
    """Base schema for rest day entries."""

    activity_type: ActivityType = Field(default=ActivityType.REST_DAY, description="Activity type")
    rest_type: str = Field(..., description="Type of rest (active, complete, partial)")
    planned: bool = Field(default=False, description="Whether this was a planned rest day")

    sleep_hours: float = Field(..., ge=0.0, le=24.0, description="Hours of sleep")
    sleep_quality: int = Field(..., ge=1, le=10, description="Sleep quality 1-10")


class RestDayEntryCreate(RestDayEntryBase):
    """Schema for creating a rest day entry."""

    # Recovery activities
    recovery_activities: list[str] | None = Field(None, description="Recovery activities performed")

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
    # processing_duration: float | None
    # data_quality_score: float | None
    # manual_overrides: dict[str, Any] | None
    # validation_notes: str | None
    energy_level: int | None
    notes: str | None
