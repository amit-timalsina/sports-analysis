from datetime import time
from typing import Any

from pydantic import Field

from common.schemas import AppBaseModel, PrimaryKeyBase, TimestampBase
from common.schemas.activity import ActivityEntryBase
from fitness_tracking.schemas.enums import MatchFormat
from fitness_tracking.schemas.enums.activity_type import ActivityType


class CricketMatchEntryBase(ActivityEntryBase):
    """Base schema for cricket match entries."""

    activity_type: ActivityType = Field(
        default=ActivityType.CRICKET_MATCH,
        description="Activity type",
    )
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
