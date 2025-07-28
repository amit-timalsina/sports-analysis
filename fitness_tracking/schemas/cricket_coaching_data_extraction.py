from typing import Literal

from pydantic import Field

from common.schemas import AppBaseModel
from fitness_tracking.schemas.enums.coaching_focus_type import CoachingFocus
from fitness_tracking.schemas.enums.cricket_discipline_type import CricketDiscipline


class CricketCoachingDataExtraction(AppBaseModel):
    """Schema for structured cricket coaching data extraction from voice input."""

    session_type: Literal["batting", "bowling", "fielding", "fitness", "mental"] | None = Field(
        None,
        description="Type of coaching session",
    )
    primary_focus: CoachingFocus | None = Field(None, description="Primary focus of the session")
    discipline_focus: CricketDiscipline | None = Field(None, description="Cricket discipline focus")
    coach_name: str | None = Field(None, description="Name of the coach")

    duration_minutes: int | None = Field(None, ge=5, le=480, description="Duration in minutes")
    what_went_well: str | None = Field(None, description="What went well in the session")
    areas_for_improvement: str | None = Field(None, description="Areas needing improvement")
    self_assessment_score: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Self-assessment score",
    )
    confidence_level: str | None = Field(None, description="Confidence level description")
    focus_level: str | None = Field(None, description="Focus level description")
    learning_satisfaction: str | None = Field(None, description="Learning satisfaction")
    mental_state: str | None = Field(None, description="Mental state during session")
    coach_feedback: str | None = Field(None, description="Feedback from coach")
    skills_practiced: list[str] | None = Field(None, description="Skills practiced")
    notes: str | None = Field(None, description="Additional notes")
