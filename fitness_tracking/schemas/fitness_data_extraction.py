"""Schema for structured fitness data extraction from voice input using LLM."""

from pydantic import Field

from common.schemas import AppBaseModel
from fitness_tracking.schemas.enums.exercise_type import ExerciseType
from fitness_tracking.schemas.enums.intensity_level import IntensityLevel


class FitnessDataExtraction(AppBaseModel):
    """Structured fitness data extraction from transcript."""

    exercise_type: ExerciseType | None = Field(None, description="Type of exercise")
    exercise_name: str | None = Field(None, description="Name of the exercise")
    duration_minutes: int | None = Field(None, gt=0, description="Duration in minutes")
    intensity: IntensityLevel | None = Field(None, description="Intensity level")

    calories_burned: int | None = Field(None, ge=1, description="Estimated calories burned")
    distance_km: float | None = Field(None, ge=0, description="Distance covered in kilometers")
    mental_state: str | None = Field(None, description="Mental state during exercise")
    energy_level: int | None = Field(
        None, ge=1, le=10, description="Energy level 1-10 during activity."
    )
    location: str | None = Field(None, description="Location where activity was performed")
