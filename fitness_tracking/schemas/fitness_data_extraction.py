"""Schema for structured fitness data extraction from voice input using LLM."""

from typing import Literal

from pydantic import Field

from common.schemas import AppBaseModel


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
