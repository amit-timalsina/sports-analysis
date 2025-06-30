"""Cricket tracking Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from common.config.settings import settings
from common.schemas import AppBaseModel


# Cricket Coaching Schemas
class CricketCoachingEntryCreate(AppBaseModel):
    """Schema for creating cricket coaching session entries."""

    session_type: Literal[
        "batting_drills",
        "wicket_keeping",
        "netting",
        "personal_coaching",
        "team_practice",
        "other",
    ]
    duration_minutes: int = Field(
        ...,
        ge=settings.validation.min_fitness_duration_minutes,
        le=settings.validation.max_fitness_duration_minutes,
        description="Duration in minutes",
    )
    what_went_well: str = Field(
        ...,
        min_length=settings.validation.min_text_length,
        max_length=settings.validation.max_text_length,
        description="What went well in the session",
    )
    areas_for_improvement: str = Field(
        ...,
        min_length=settings.validation.min_text_length,
        max_length=settings.validation.max_text_length,
        description="Areas that need improvement",
    )
    coach_feedback: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Coach feedback if available",
    )
    self_assessment_score: int = Field(..., ge=1, le=10, description="Self-assessment score 1-10")

    # Technical focus areas
    skills_practiced: str = Field(
        ...,
        min_length=settings.validation.min_text_length,
        max_length=settings.validation.max_text_length,
        description="Skills practiced during session",
    )
    time_per_skill: str | None = Field(None, max_length=500, description="Time spent on each skill")
    difficulty_level: int = Field(..., ge=1, le=10, description="Difficulty level of exercises")

    # Mental state during session
    confidence_level: int = Field(..., ge=1, le=10, description="Confidence level during session")
    focus_level: int = Field(..., ge=1, le=10, description="Focus level during session")
    learning_satisfaction: int = Field(..., ge=1, le=10, description="Learning satisfaction")
    frustration_points: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Points of frustration",
    )

    # Common fields
    mental_state: Literal["excellent", "good", "okay", "poor"]
    notes: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Additional notes",
    )


class CricketCoachingEntryRead(AppBaseModel):
    """Schema for reading cricket coaching session entries."""

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
    # Timestamps
    created_at: datetime
    updated_at: datetime | None


class CricketCoachingEntryUpdate(AppBaseModel):
    """Schema for updating cricket coaching session entries."""

    session_type: (
        Literal[
            "batting_drills",
            "wicket_keeping",
            "netting",
            "personal_coaching",
            "team_practice",
            "other",
        ]
        | None
    ) = None
    duration_minutes: int | None = Field(
        None,
        ge=settings.validation.min_fitness_duration_minutes,
        le=settings.validation.max_fitness_duration_minutes,
        description="Duration in minutes",
    )
    what_went_well: str | None = Field(
        None,
        min_length=settings.validation.min_text_length,
        max_length=settings.validation.max_text_length,
        description="What went well in the session",
    )
    areas_for_improvement: str | None = Field(
        None,
        min_length=settings.validation.min_text_length,
        max_length=settings.validation.max_text_length,
        description="Areas that need improvement",
    )
    coach_feedback: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Coach feedback if available",
    )
    self_assessment_score: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Self-assessment score 1-10",
    )
    skills_practiced: str | None = Field(
        None,
        min_length=settings.validation.min_text_length,
        max_length=settings.validation.max_text_length,
        description="Skills practiced during session",
    )
    time_per_skill: str | None = Field(None, max_length=500, description="Time spent on each skill")
    difficulty_level: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Difficulty level of exercises",
    )
    confidence_level: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Confidence level during session",
    )
    focus_level: int | None = Field(None, ge=1, le=10, description="Focus level during session")
    learning_satisfaction: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Learning satisfaction",
    )
    frustration_points: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Points of frustration",
    )
    mental_state: Literal["excellent", "good", "okay", "poor"] | None = None
    notes: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Additional notes",
    )


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
    """Schema for structured cricket coaching data extraction from voice."""

    session_type: Literal[
        "batting_drills",
        "wicket_keeping",
        "netting",
        "personal_coaching",
        "team_practice",
        "other",
    ] = Field(
        ...,
        description="Type of cricket session - must be one of the valid session types",
    )
    duration_minutes: int = Field(..., description="Duration in minutes")
    what_went_well: str = Field(..., description="What went well in the session")
    areas_for_improvement: str = Field(..., description="Areas that need improvement")
    skills_practiced: str = Field(..., description="Skills practiced during session")
    self_assessment_score: int = Field(..., ge=1, le=10, description="Self-assessment score 1-10")
    confidence_level: int = Field(..., ge=1, le=10, description="Confidence level during session")
    focus_level: int = Field(..., ge=1, le=10, description="Focus level during session")
    mental_state: str = Field(..., description="Mental state during session")

    # Optional extracted fields
    coach_feedback: str | None = Field(None, description="Coach feedback if mentioned")
    difficulty_level: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Difficulty level of exercises",
    )
    learning_satisfaction: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Learning satisfaction",
    )


# Cricket Match Schemas
class CricketMatchEntryCreate(AppBaseModel):
    """Schema for creating cricket match performance entries."""

    match_type: Literal["practice", "tournament", "school", "club", "other"]
    opposition_strength: int = Field(..., ge=1, le=10, description="Opposition strength 1-10")
    weather_conditions: str | None = Field(None, max_length=200, description="Weather conditions")
    pitch_conditions: str | None = Field(None, max_length=200, description="Pitch conditions")
    batting_order: int | None = Field(None, ge=1, le=11, description="Batting order position")

    # Batting statistics
    runs_scored: int | None = Field(None, ge=0, description="Runs scored")
    balls_faced: int | None = Field(None, ge=0, description="Balls faced")
    boundaries_4s: int | None = Field(None, ge=0, description="4s scored")
    boundaries_6s: int | None = Field(None, ge=0, description="6s scored")
    how_out: str | None = Field(None, max_length=200, description="How out (if applicable)")
    key_shots_played: str | None = Field(None, max_length=500, description="Key shots played well")
    batting_mistakes: str | None = Field(None, max_length=500, description="Batting mistakes made")

    # Wicket keeping statistics
    catches_taken: int | None = Field(None, ge=0, description="Catches taken")
    catches_dropped: int | None = Field(None, ge=0, description="Catches dropped")
    stumpings: int | None = Field(None, ge=0, description="Stumpings completed")
    byes_conceded: int | None = Field(None, ge=0, description="Byes conceded")
    keeping_key_moments: str | None = Field(None, max_length=500, description="Key keeping moments")

    # Mental state tracking
    pre_match_nerves: int = Field(..., ge=1, le=10, description="Pre-match nerves level")
    focus_during_batting: int | None = Field(None, ge=1, le=10, description="Focus during batting")
    focus_during_keeping: int | None = Field(None, ge=1, le=10, description="Focus during keeping")
    post_match_satisfaction: int = Field(..., ge=1, le=10, description="Post-match satisfaction")
    mental_challenges: str | None = Field(
        None,
        max_length=500,
        description="Mental challenges faced",
    )

    # Common fields
    mental_state: Literal["excellent", "good", "okay", "poor"]
    notes: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Additional notes",
    )


class CricketMatchEntryRead(AppBaseModel):
    """Schema for reading cricket match performance entries."""

    id: int
    session_id: str
    user_id: str
    match_type: str
    opposition_strength: int
    pre_match_nerves: int
    post_match_satisfaction: int
    mental_state: str
    runs_scored: int | None
    balls_faced: int | None
    boundaries_4s: int | None
    boundaries_6s: int | None
    how_out: str | None
    key_shots_played: str | None
    catches_taken: int | None
    catches_dropped: int | None
    stumpings: int | None
    notes: str | None
    # Voice processing metadata
    transcript: str
    confidence_score: float
    processing_duration: float | None
    # Timestamps
    created_at: datetime
    updated_at: datetime | None


class CricketMatchEntryUpdate(AppBaseModel):
    """Schema for updating cricket match performance entries."""

    match_type: Literal["practice", "tournament", "school", "club", "other"] | None = None
    opposition_strength: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Opposition strength 1-10",
    )
    weather_conditions: str | None = Field(None, max_length=200, description="Weather conditions")
    pitch_conditions: str | None = Field(None, max_length=200, description="Pitch conditions")
    batting_order: int | None = Field(None, ge=1, le=11, description="Batting order position")
    runs_scored: int | None = Field(None, ge=0, description="Runs scored")
    balls_faced: int | None = Field(None, ge=0, description="Balls faced")
    boundaries_4s: int | None = Field(None, ge=0, description="4s scored")
    boundaries_6s: int | None = Field(None, ge=0, description="6s scored")
    how_out: str | None = Field(None, max_length=200, description="How out (if applicable)")
    key_shots_played: str | None = Field(None, max_length=500, description="Key shots played well")
    batting_mistakes: str | None = Field(None, max_length=500, description="Batting mistakes made")
    catches_taken: int | None = Field(None, ge=0, description="Catches taken")
    catches_dropped: int | None = Field(None, ge=0, description="Catches dropped")
    stumpings: int | None = Field(None, ge=0, description="Stumpings completed")
    byes_conceded: int | None = Field(None, ge=0, description="Byes conceded")
    keeping_key_moments: str | None = Field(None, max_length=500, description="Key keeping moments")
    pre_match_nerves: int | None = Field(None, ge=1, le=10, description="Pre-match nerves level")
    focus_during_batting: int | None = Field(None, ge=1, le=10, description="Focus during batting")
    focus_during_keeping: int | None = Field(None, ge=1, le=10, description="Focus during keeping")
    post_match_satisfaction: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Post-match satisfaction",
    )
    mental_challenges: str | None = Field(
        None,
        max_length=500,
        description="Mental challenges faced",
    )
    mental_state: Literal["excellent", "good", "okay", "poor"] | None = None
    notes: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Additional notes",
    )


class CricketMatchEntryResponse(AppBaseModel):
    """Schema for cricket match entry responses."""

    id: int
    session_id: str
    user_id: str
    match_type: str
    opposition_strength: int
    weather_conditions: str | None
    pitch_conditions: str | None
    batting_order: int | None
    runs_scored: int | None
    balls_faced: int | None
    boundaries_4s: int | None
    boundaries_6s: int | None
    how_out: str | None
    key_shots_played: str | None
    batting_mistakes: str | None
    catches_taken: int | None
    catches_dropped: int | None
    stumpings: int | None
    byes_conceded: int | None
    keeping_key_moments: str | None
    pre_match_nerves: int
    focus_during_batting: int | None
    focus_during_keeping: int | None
    post_match_satisfaction: int
    mental_challenges: str | None
    mental_state: str
    notes: str | None
    # Voice processing metadata
    transcript: str
    confidence_score: float
    processing_duration: float | None


class CricketMatchDataExtraction(AppBaseModel):
    """Schema for structured cricket match data extraction from voice."""

    match_type: Literal["practice", "tournament", "school", "club", "other"] = Field(
        ...,
        description="Type of match - must be one of the valid match types",
    )
    opposition_strength: int = Field(..., ge=1, le=10, description="Opposition strength 1-10")
    pre_match_nerves: int = Field(..., ge=1, le=10, description="Pre-match nerves level")
    post_match_satisfaction: int = Field(..., ge=1, le=10, description="Post-match satisfaction")
    mental_state: str = Field(..., description="Overall mental state during match")

    # Optional batting statistics
    runs_scored: int | None = Field(None, ge=0, description="Runs scored")
    balls_faced: int | None = Field(None, ge=0, description="Balls faced")
    boundaries_4s: int | None = Field(None, ge=0, description="4s scored")
    boundaries_6s: int | None = Field(None, ge=0, description="6s scored")
    how_out: str | None = Field(None, description="How out (if applicable)")
    key_shots_played: str | None = Field(None, description="Key shots played well")

    # Optional keeping statistics
    catches_taken: int | None = Field(None, ge=0, description="Catches taken")
    catches_dropped: int | None = Field(None, ge=0, description="Catches dropped")
    stumpings: int | None = Field(None, ge=0, description="Stumpings completed")


# Rest Day Schemas
class RestDayEntryCreate(AppBaseModel):
    """Schema for creating rest day entries."""

    rest_type: Literal["complete_rest", "active_recovery", "injury_recovery"]
    physical_state: str = Field(
        ...,
        min_length=settings.validation.min_text_length,
        max_length=settings.validation.max_text_length,
        description="Physical state during rest",
    )
    fatigue_level: int = Field(..., ge=1, le=10, description="Fatigue level 1-10")
    energy_level: int = Field(..., ge=1, le=10, description="Energy level 1-10")
    soreness_level: int = Field(..., ge=1, le=10, description="Muscle soreness level 1-10")

    # Mental state
    motivation_level: int = Field(..., ge=1, le=10, description="Motivation level 1-10")
    mood_description: str = Field(
        ...,
        min_length=settings.validation.min_text_length,
        max_length=settings.validation.max_text_length,
        description="Mood description",
    )

    # Reflections
    training_reflections: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Reflections on training",
    )
    goals_concerns: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Goals and concerns",
    )
    recovery_activities: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Recovery activities done",
    )

    # Common fields
    mental_state: Literal["excellent", "good", "okay", "poor"]
    notes: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Additional notes",
    )


class RestDayEntryRead(AppBaseModel):
    """Schema for reading rest day entries."""

    id: int
    session_id: str
    user_id: str
    rest_type: str
    physical_state: str
    fatigue_level: int
    energy_level: int
    soreness_level: int | None
    motivation_level: int
    mood_description: str
    training_reflections: str | None
    goals_concerns: str | None
    recovery_activities: str | None
    mental_state: str
    notes: str | None
    # Voice processing metadata
    transcript: str
    confidence_score: float
    processing_duration: float | None
    # Timestamps
    created_at: datetime
    updated_at: datetime | None


class RestDayEntryUpdate(AppBaseModel):
    """Schema for updating rest day entries."""

    rest_type: Literal["complete_rest", "active_recovery", "injury_recovery"] | None = None
    physical_state: str | None = Field(
        None,
        min_length=settings.validation.min_text_length,
        max_length=settings.validation.max_text_length,
        description="Physical state during rest",
    )
    fatigue_level: int | None = Field(None, ge=1, le=10, description="Fatigue level 1-10")
    energy_level: int | None = Field(None, ge=1, le=10, description="Energy level 1-10")
    soreness_level: int | None = Field(None, ge=1, le=10, description="Muscle soreness level 1-10")
    motivation_level: int | None = Field(None, ge=1, le=10, description="Motivation level 1-10")
    mood_description: str | None = Field(
        None,
        min_length=settings.validation.min_text_length,
        max_length=settings.validation.max_text_length,
        description="Mood description",
    )
    training_reflections: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Reflections on training",
    )
    goals_concerns: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Goals and concerns",
    )
    recovery_activities: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Recovery activities done",
    )
    mental_state: Literal["excellent", "good", "okay", "poor"] | None = None
    notes: str | None = Field(
        None,
        max_length=settings.validation.max_text_length,
        description="Additional notes",
    )


class RestDayEntryResponse(AppBaseModel):
    """Schema for rest day entry responses."""

    id: int
    session_id: str
    user_id: str
    rest_type: str
    physical_state: str
    fatigue_level: int
    energy_level: int
    soreness_level: int
    motivation_level: int
    mood_description: str
    training_reflections: str | None
    goals_concerns: str | None
    recovery_activities: str | None
    mental_state: str
    notes: str | None
    # Voice processing metadata
    transcript: str
    confidence_score: float
    processing_duration: float | None


class RestDayDataExtraction(AppBaseModel):
    """Schema for structured rest day data extraction from voice."""

    rest_type: Literal["complete_rest", "active_recovery", "injury_recovery"] = Field(
        ...,
        description="Type of rest day - must be one of the valid rest types",
    )
    physical_state: str = Field(..., description="Physical state during rest")
    fatigue_level: int = Field(..., ge=1, le=10, description="Fatigue level 1-10")
    energy_level: int = Field(..., ge=1, le=10, description="Energy level 1-10")
    motivation_level: int = Field(..., ge=1, le=10, description="Motivation level 1-10")
    mood_description: str = Field(..., description="Mood description")
    mental_state: str = Field(..., description="Overall mental state during rest")

    # Optional extracted fields
    soreness_level: int | None = Field(None, ge=1, le=10, description="Muscle soreness level 1-10")
    training_reflections: str | None = Field(None, description="Reflections on training")
    goals_concerns: str | None = Field(None, description="Goals and concerns")
    recovery_activities: str | None = Field(None, description="Recovery activities done")


# Analytics Schemas
class CricketAnalytics(AppBaseModel):
    """Schema for cricket analytics and insights."""

    total_coaching_sessions: int
    total_matches: int
    total_rest_days: int
    average_self_assessment: float
    batting_average: float | None
    keeping_success_rate: float | None
    most_practiced_skill: str
    confidence_trend: dict[str, float]
    improvement_areas: list[str]
    recommendations: list[str]


class CombinedAnalytics(AppBaseModel):
    """Schema for combined fitness and cricket analytics."""

    fitness_analytics: dict[str, float]  # FitnessAnalytics data
    cricket_analytics: CricketAnalytics
    correlations: dict[str, float]  # Fitness-cricket performance correlations
    overall_recommendations: list[str]
