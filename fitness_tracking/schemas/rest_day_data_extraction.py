from pydantic import Field

from common.schemas import AppBaseModel


class RestDayDataExtraction(AppBaseModel):
    """Schema for structured rest day data extraction from voice."""

    rest_type: str | None = Field(
        None,
        description="Type of rest day. Must be exactly one of: complete_rest, active_recovery, injury_recovery. Map similar terms: full rest/total rest -> complete_rest, light activity -> active_recovery, hurt/injured -> injury_recovery.",
    )
    sleep_hours: float = Field(..., ge=0.0, le=24.0, description="Hours of sleep")

    sleep_quality: int = Field(..., ge=1, le=10, description="Sleep quality 1-10")

    planned: bool = Field(default=False, description="Whether this was a planned rest day")
    physical_state: str | None = Field(None, description="Physical state during rest")
    fatigue_level: str | None = Field(
        None,
        description="Fatigue level - use descriptive terms like 'exhausted', 'tired', 'okay', 'fresh', 'energetic'",
    )
    energy_level: str | None = Field(
        None,
        description="Energy level - use descriptive terms like 'very low', 'low', 'average', 'high', 'very high'",
    )
    motivation_level: str | None = Field(
        None,
        description="Motivation level - use descriptive terms like 'unmotivated', 'low', 'motivated', 'very motivated'",
    )
    mood_description: str | None = Field(None, description="Mood description")
    mental_state: str | None = Field(None, description="Overall mental state during rest")

    # Optional extracted fields
    soreness_level: str | None = Field(
        None,
        description="Muscle soreness level - use descriptive terms like 'very sore', 'sore', 'a bit sore', 'fine'",
    )
    training_reflections: str | None = Field(None, description="Reflections on training")
    goals_concerns: str | None = Field(None, description="Goals and concerns")
    recovery_activities: str | None = Field(None, description="Recovery activities done")
    notes: str | None = Field(None, description="Additional notes about the rest day")
