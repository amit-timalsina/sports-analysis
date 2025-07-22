"""Cricket tracking Pydantic schemas."""

from datetime import time
from typing import Any, Literal

from pydantic import Field

from common.schemas import AppBaseModel, PrimaryKeyBase, TimestampBase
from common.schemas.activity import ActivityEntryBase
from fitness_tracking.schemas.enums.activity_type import ActivityType
from fitness_tracking.schemas.enums.coaching_focus_type import CoachingFocus
from fitness_tracking.schemas.enums.cricket_discipline_type import CricketDiscipline


# Cricket Coaching Schemas
class CricketCoachingEntryBase(ActivityEntryBase):
    """Base schema for cricket coaching entries."""

    activity_type: ActivityType = Field(
        default=ActivityType.CRICKET_COACHING,
        description="Activity type",
    )
    coach_name: str = Field(..., description="Name of the coach")
    session_type: str = Field(..., description="Type of session (individual, group, masterclass)")
    duration_minutes: int = Field(..., gt=0, description="Duration in minutes")
    primary_focus: CoachingFocus = Field(..., description="Primary focus of the session")
    skills_practiced: list[str] = Field(default_factory=list, description="Skills practiced")
    discipline_focus: CricketDiscipline = Field(..., description="Cricket discipline focus")


class CricketCoachingEntryCreate(CricketCoachingEntryBase):
    """Schema for creating a cricket coaching entry."""

    secondary_focus: CoachingFocus | None = Field(
        None,
        description="Secondary focus of the session",
    )

    # Session structure
    warm_up_minutes: int | None = Field(None, ge=0, description="Warm-up time in minutes")
    skill_work_minutes: int | None = Field(None, ge=0, description="Skill work time in minutes")
    game_simulation_minutes: int | None = Field(None, ge=0, description="Game simulation time")
    cool_down_minutes: int | None = Field(None, ge=0, description="Cool-down time in minutes")

    # Equipment and setup
    equipment_used: list[str] | None = Field(None, description="Equipment used during session")
    facility_name: str | None = Field(None, description="Name of the facility")
    indoor_outdoor: str | None = Field(None, description="Indoor or outdoor session")

    # Performance tracking
    technique_rating: int | None = Field(None, ge=1, le=10, description="Technique rating 1-10")
    effort_level: int | None = Field(None, ge=1, le=10, description="Effort level 1-10")
    coach_feedback: str | None = Field(None, description="Coach feedback")
    improvement_areas: list[str] | None = Field(None, description="Areas for improvement")

    # Goals and targets
    session_goals: list[str] | None = Field(None, description="Goals for the session")
    goals_achieved: list[str] | None = Field(None, description="Goals achieved")
    next_session_focus: str | None = Field(None, description="Focus for next session")

    # Cost and logistics
    session_cost: float | None = Field(None, ge=0.0, description="Cost of the session")
    group_size: int | None = Field(None, ge=1, description="Number of people in group")

    # Timing
    start_time: time | None = Field(None, description="Session start time")
    end_time: time | None = Field(None, description="Session end time")

    # Data quality tracking
    processing_duration: float | None = Field(None, ge=0.0, description="Processing duration")
    data_quality_score: float | None = Field(None, ge=0.0, le=1.0, description="Data quality score")
    manual_overrides: dict[str, Any] | None = Field(None, description="Manual data overrides")
    validation_notes: str | None = Field(None, description="Validation notes")
    energy_level: int | None = Field(None, ge=1, le=10, description="Energy level 1-10")
    notes: str | None = Field(None, description="Additional notes")


class CricketCoachingEntryRead(PrimaryKeyBase, TimestampBase, CricketCoachingEntryBase):
    """Schema for reading cricket coaching entry data."""

    secondary_focus: CoachingFocus | None
    warm_up_minutes: int | None
    skill_work_minutes: int | None
    game_simulation_minutes: int | None
    cool_down_minutes: int | None
    equipment_used: list[str] | None
    facility_name: str | None
    indoor_outdoor: str | None
    technique_rating: int | None
    effort_level: int | None
    coach_feedback: str | None
    improvement_areas: list[str] | None
    session_goals: list[str] | None
    goals_achieved: list[str] | None
    next_session_focus: str | None
    session_cost: float | None
    group_size: int | None
    start_time: time | None
    end_time: time | None
    processing_duration: float | None
    data_quality_score: float | None
    manual_overrides: dict[str, Any] | None
    validation_notes: str | None
    energy_level: int | None
    notes: str | None


class CricketCoachingEntryUpdate(AppBaseModel):
    """Schema for updating a cricket coaching entry."""

    coach_name: str | None = None
    session_type: str | None = None
    duration_minutes: int | None = Field(None, gt=0)
    primary_focus: CoachingFocus | None = None
    secondary_focus: CoachingFocus | None = None
    skills_practiced: list[str] | None = None
    discipline_focus: CricketDiscipline | None = None
    warm_up_minutes: int | None = Field(None, ge=0)
    skill_work_minutes: int | None = Field(None, ge=0)
    game_simulation_minutes: int | None = Field(None, ge=0)
    cool_down_minutes: int | None = Field(None, ge=0)
    equipment_used: list[str] | None = None
    facility_name: str | None = None
    indoor_outdoor: str | None = None
    technique_rating: int | None = Field(None, ge=1, le=10)
    effort_level: int | None = Field(None, ge=1, le=10)
    coach_feedback: str | None = None
    improvement_areas: list[str] | None = None
    session_goals: list[str] | None = None
    goals_achieved: list[str] | None = None
    next_session_focus: str | None = None
    session_cost: float | None = Field(None, ge=0.0)
    group_size: int | None = Field(None, ge=1)
    start_time: time | None = None
    end_time: time | None = None
    data_quality_score: float | None = Field(None, ge=0.0, le=1.0)
    manual_overrides: dict[str, Any] | None = None
    validation_notes: str | None = None
    energy_level: int | None = Field(None, ge=1, le=10)
    notes: str | None = None


class CricketCoachingEntryResponse(AppBaseModel):
    """Schema for cricket coaching entry responses."""

    id: int
    session_id: str
    user_id: str
    session_type: str
    duration_minutes: int
    what_went_well: str
    areas_for_improvement: str
    coach_feedback: str | None
    self_assessment_score: int
    skills_practiced: str
    time_per_skill: str | None
    difficulty_level: int
    confidence_level: int
    focus_level: int
    learning_satisfaction: int
    frustration_points: str | None
    mental_state: str
    notes: str | None
    # Voice processing metadata
    transcript: str
    confidence_score: float
    processing_duration: float | None


class CricketCoachingDataExtraction(AppBaseModel):
    """Schema for structured cricket coaching data extraction from voice input."""

    session_type: Literal["batting", "bowling", "fielding", "fitness", "mental"] | None = Field(
        None,
        description="Type of coaching session",
    )
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
