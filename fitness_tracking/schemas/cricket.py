"""Cricket tracking Pydantic schemas."""

from datetime import datetime, time
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from common.config.settings import settings
from common.schemas import AppBaseModel, PrimaryKeyBase, TimestampBase
from common.schemas.activity import ActivityEntryBase
from common.schemas.entry_type import EntryType
from fitness_tracking.schemas.cricket_enums import (
    CoachingFocus,
    CricketDiscipline,
    MatchFormat,
)


# Cricket Coaching Schemas
class CricketCoachingEntryBase(ActivityEntryBase):
    """Base schema for cricket coaching entries."""

    entry_type: EntryType = Field(default=EntryType.CRICKET_COACHING, description="Entry type")
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


# Cricket Match Schemas
class CricketMatchEntryBase(ActivityEntryBase):
    """Base schema for cricket match entries."""

    entry_type: EntryType = Field(default=EntryType.CRICKET_MATCH, description="Entry type")
    match_format: MatchFormat = Field(..., description="Format of the match")
    opposition_team: str = Field(..., description="Name of the opposition team")
    venue: str = Field(..., description="Match venue")
    home_away: str = Field(..., description="Home, away, or neutral venue")
    result: str = Field(..., description="Match result (won, lost, draw, no_result)")
    team_name: str = Field(..., description="Your team name")


class CricketMatchEntryCreate(CricketMatchEntryBase):
    """Schema for creating a cricket match entry."""

    # Team performance
    team_total: int | None = Field(None, ge=0, description="Team total score")
    team_wickets: int | None = Field(None, ge=0, le=10, description="Team wickets lost")
    team_overs: float | None = Field(None, ge=0.0, description="Team overs played")
    opposition_total: int | None = Field(None, ge=0, description="Opposition total score")
    opposition_wickets: int | None = Field(None, ge=0, le=10, description="Opposition wickets lost")
    opposition_overs: float | None = Field(None, ge=0.0, description="Opposition overs played")

    # Personal batting performance
    batting_position: int | None = Field(None, ge=1, le=11, description="Batting position")
    runs_scored: int | None = Field(None, ge=0, description="Runs scored")
    balls_faced: int | None = Field(None, ge=0, description="Balls faced")
    boundaries: int | None = Field(None, ge=0, description="Number of boundaries (4s)")
    sixes: int | None = Field(None, ge=0, description="Number of sixes")
    dismissal_type: str | None = Field(None, description="How you were dismissed")
    strike_rate: float | None = Field(None, ge=0.0, description="Strike rate")

    # Personal bowling performance
    overs_bowled: float | None = Field(None, ge=0.0, description="Overs bowled")
    runs_conceded: int | None = Field(None, ge=0, description="Runs conceded while bowling")
    wickets_taken: int | None = Field(None, ge=0, description="Wickets taken")
    economy_rate: float | None = Field(None, ge=0.0, description="Economy rate")
    best_bowling: str | None = Field(None, description="Best bowling figures")

    # Personal fielding performance
    catches_taken: int | None = Field(None, ge=0, description="Catches taken")
    run_outs: int | None = Field(None, ge=0, description="Run outs effected")
    stumpings: int | None = Field(None, ge=0, description="Stumpings (if wicket keeper)")
    fielding_position: str | None = Field(None, description="Fielding position")

    # Match conditions
    weather_conditions: str | None = Field(None, description="Weather conditions")
    pitch_conditions: str | None = Field(None, description="Pitch conditions")
    toss_won_by: str | None = Field(None, description="Who won the toss")
    elected_to: str | None = Field(None, description="Elected to bat or bowl")

    # Performance ratings
    batting_performance: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Batting performance 1-10",
    )
    bowling_performance: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Bowling performance 1-10",
    )
    fielding_performance: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Fielding performance 1-10",
    )
    overall_performance: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Overall performance 1-10",
    )

    # Key moments and learnings
    key_moments: list[str] | None = Field(None, description="Key moments in the match")
    what_went_well: list[str] | None = Field(None, description="What went well")
    areas_for_improvement: list[str] | None = Field(None, description="Areas for improvement")
    captain_feedback: str | None = Field(None, description="Captain's feedback")
    coach_feedback: str | None = Field(None, description="Coach's feedback")

    # Match logistics
    match_duration_hours: float | None = Field(None, ge=0.0, description="Match duration in hours")
    start_time: time | None = Field(None, description="Match start time")
    end_time: time | None = Field(None, description="Match end time")
    match_fee: float | None = Field(None, ge=0.0, description="Match fee received")
    travel_distance_km: float | None = Field(None, ge=0.0, description="Travel distance")

    # Data quality tracking
    processing_duration: float | None = Field(None, ge=0.0, description="Processing duration")
    data_quality_score: float | None = Field(None, ge=0.0, le=1.0, description="Data quality score")
    manual_overrides: dict[str, Any] | None = Field(None, description="Manual data overrides")
    validation_notes: str | None = Field(None, description="Validation notes")
    energy_level: int | None = Field(None, ge=1, le=10, description="Energy level 1-10")
    notes: str | None = Field(None, description="Additional notes")


class CricketMatchEntryUpdate(AppBaseModel):
    """Schema for updating a cricket match entry."""

    match_format: MatchFormat | None = None
    opposition_team: str | None = None
    venue: str | None = None
    home_away: str | None = None
    result: str | None = None
    team_name: str | None = None
    team_total: int | None = Field(None, ge=0)
    team_wickets: int | None = Field(None, ge=0, le=10)
    team_overs: float | None = Field(None, ge=0.0)
    opposition_total: int | None = Field(None, ge=0)
    opposition_wickets: int | None = Field(None, ge=0, le=10)
    opposition_overs: float | None = Field(None, ge=0.0)
    batting_position: int | None = Field(None, ge=1, le=11)
    runs_scored: int | None = Field(None, ge=0)
    balls_faced: int | None = Field(None, ge=0)
    boundaries: int | None = Field(None, ge=0)
    sixes: int | None = Field(None, ge=0)
    dismissal_type: str | None = None
    strike_rate: float | None = Field(None, ge=0.0)
    overs_bowled: float | None = Field(None, ge=0.0)
    runs_conceded: int | None = Field(None, ge=0)
    wickets_taken: int | None = Field(None, ge=0)
    economy_rate: float | None = Field(None, ge=0.0)
    best_bowling: str | None = None
    catches_taken: int | None = Field(None, ge=0)
    run_outs: int | None = Field(None, ge=0)
    stumpings: int | None = Field(None, ge=0)
    fielding_position: str | None = None
    weather_conditions: str | None = None
    pitch_conditions: str | None = None
    toss_won_by: str | None = None
    elected_to: str | None = None
    batting_performance: int | None = Field(None, ge=1, le=10)
    bowling_performance: int | None = Field(None, ge=1, le=10)
    fielding_performance: int | None = Field(None, ge=1, le=10)
    overall_performance: int | None = Field(None, ge=1, le=10)
    key_moments: list[str] | None = None
    what_went_well: list[str] | None = None
    areas_for_improvement: list[str] | None = None
    captain_feedback: str | None = None
    coach_feedback: str | None = None
    match_duration_hours: float | None = Field(None, ge=0.0)
    start_time: time | None = None
    end_time: time | None = None
    match_fee: float | None = Field(None, ge=0.0)
    travel_distance_km: float | None = Field(None, ge=0.0)
    data_quality_score: float | None = Field(None, ge=0.0, le=1.0)
    manual_overrides: dict[str, Any] | None = None
    validation_notes: str | None = None
    energy_level: int | None = Field(None, ge=1, le=10)
    notes: str | None = None


class CricketMatchEntryRead(PrimaryKeyBase, TimestampBase, CricketMatchEntryBase):
    """Schema for reading cricket match entry data."""

    team_total: int | None
    team_wickets: int | None
    team_overs: float | None
    opposition_total: int | None
    opposition_wickets: int | None
    opposition_overs: float | None
    batting_position: int | None
    runs_scored: int | None
    balls_faced: int | None
    boundaries: int | None
    sixes: int | None
    dismissal_type: str | None
    strike_rate: float | None
    overs_bowled: float | None
    runs_conceded: int | None
    wickets_taken: int | None
    economy_rate: float | None
    best_bowling: str | None
    catches_taken: int | None
    run_outs: int | None
    stumpings: int | None
    fielding_position: str | None
    weather_conditions: str | None
    pitch_conditions: str | None
    toss_won_by: str | None
    elected_to: str | None
    batting_performance: int | None
    bowling_performance: int | None
    fielding_performance: int | None
    overall_performance: int | None
    key_moments: list[str] | None
    what_went_well: list[str] | None
    areas_for_improvement: list[str] | None
    captain_feedback: str | None
    coach_feedback: str | None
    match_duration_hours: float | None
    start_time: time | None
    end_time: time | None
    match_fee: float | None
    travel_distance_km: float | None
    processing_duration: float | None
    data_quality_score: float | None
    manual_overrides: dict[str, Any] | None
    validation_notes: str | None
    energy_level: int | None
    notes: str | None


class CricketMatchDataExtraction(AppBaseModel):
    """Schema for structured cricket match data extraction from voice input."""

    match_type: Literal["tournament", "practice", "friendly"] | None = Field(
        None,
        description="Type of match",
    )
    opposition_strength: str | None = Field(None, description="Opposition strength description")
    runs_scored: int | None = Field(None, ge=0, description="Runs scored")
    balls_faced: int | None = Field(None, ge=0, description="Balls faced")
    boundaries_4s: int | None = Field(None, ge=0, description="Number of 4s hit")
    boundaries_6s: int | None = Field(None, ge=0, description="Number of 6s hit")
    how_out: str | None = Field(None, description="How the player got out")
    key_shots_played: str | None = Field(None, description="Key shots played")
    catches_taken: int | None = Field(None, ge=0, description="Catches taken")
    catches_dropped: int | None = Field(None, ge=0, description="Catches dropped")
    stumpings: int | None = Field(None, ge=0, description="Stumpings made")
    pre_match_nerves: str | None = Field(None, description="Pre-match nerves description")
    post_match_satisfaction: str | None = Field(None, description="Post-match satisfaction")
    mental_state: str | None = Field(None, description="Mental state during match")
    notes: str | None = Field(None, description="Additional notes")


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

    id: UUID
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

    id: UUID
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

    rest_type: str = Field(
        ...,
        description="Type of rest day. Must be exactly one of: complete_rest, active_recovery, injury_recovery. Map similar terms: full rest/total rest -> complete_rest, light activity -> active_recovery, hurt/injured -> injury_recovery.",
    )
    physical_state: str = Field(..., description="Physical state during rest")
    fatigue_level: str = Field(
        ...,
        description="Fatigue level - use descriptive terms like 'exhausted', 'tired', 'okay', 'fresh', 'energetic'",
    )
    energy_level: str = Field(
        ...,
        description="Energy level - use descriptive terms like 'very low', 'low', 'average', 'high', 'very high'",
    )
    motivation_level: str = Field(
        ...,
        description="Motivation level - use descriptive terms like 'unmotivated', 'low', 'motivated', 'very motivated'",
    )
    mood_description: str = Field(..., description="Mood description")
    mental_state: str = Field(..., description="Overall mental state during rest")

    # Optional extracted fields
    soreness_level: str | None = Field(
        None,
        description="Muscle soreness level - use descriptive terms like 'very sore', 'sore', 'a bit sore', 'fine'",
    )
    training_reflections: str | None = Field(None, description="Reflections on training")
    goals_concerns: str | None = Field(None, description="Goals and concerns")
    recovery_activities: str | None = Field(None, description="Recovery activities done")
    notes: str | None = Field(None, description="Additional notes about the rest day")


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
