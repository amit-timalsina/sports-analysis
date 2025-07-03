"""Cricket activity tracking SQLAlchemy 2.0 models."""

from datetime import time

from sqlalchemy import JSON, String
from sqlalchemy import Enum as SA_Enum
from sqlalchemy.orm import Mapped, mapped_column

from common.models.activity import ActivityEntryBase
from common.schemas.entry_type import EntryType
from fitness_tracking.schemas.cricket_enums import CoachingFocus, CricketDiscipline, MatchFormat


class CricketCoachingEntry(ActivityEntryBase):
    """SQLAlchemy 2.0 model for cricket coaching session entries."""

    __tablename__ = "cricket_coaching_entries"

    # Set the entry type
    entry_type: Mapped[EntryType] = mapped_column(
        SA_Enum(EntryType),
        default=EntryType.CRICKET_COACHING,
        index=True,
    )

    # Core cricket fields (match DB schema)
    coach_name: Mapped[str] = mapped_column(String)
    session_type: Mapped[str] = mapped_column(String)
    duration_minutes: Mapped[int] = mapped_column()
    primary_focus: Mapped[CoachingFocus | None] = mapped_column(SA_Enum(CoachingFocus))
    secondary_focus: Mapped[CoachingFocus | None] = mapped_column(SA_Enum(CoachingFocus))
    skills_practiced: Mapped[list[str]] = mapped_column(JSON)
    discipline_focus: Mapped[CricketDiscipline | None] = mapped_column(SA_Enum(CricketDiscipline))

    # Session structure
    warm_up_minutes: Mapped[int | None] = mapped_column()
    skill_work_minutes: Mapped[int | None] = mapped_column()
    game_simulation_minutes: Mapped[int | None] = mapped_column()
    cool_down_minutes: Mapped[int | None] = mapped_column()

    # Equipment and setup
    equipment_used: Mapped[list[str] | None] = mapped_column(JSON)
    facility_name: Mapped[str | None] = mapped_column(String)
    indoor_outdoor: Mapped[str | None] = mapped_column(String)

    # Performance tracking
    technique_rating: Mapped[int | None] = mapped_column()
    effort_level: Mapped[int | None] = mapped_column()
    coach_feedback: Mapped[str | None] = mapped_column(String)
    improvement_areas: Mapped[list[str] | None] = mapped_column(JSON)

    # Goals and targets
    session_goals: Mapped[list[str] | None] = mapped_column(JSON)
    goals_achieved: Mapped[list[str] | None] = mapped_column(JSON)
    next_session_focus: Mapped[str | None] = mapped_column(String)

    # Cost and logistics
    session_cost: Mapped[float | None] = mapped_column()
    group_size: Mapped[int | None] = mapped_column()

    # Timing
    start_time: Mapped[time | None] = mapped_column()
    end_time: Mapped[time | None] = mapped_column()


class CricketMatchEntry(ActivityEntryBase):
    """SQLAlchemy 2.0 model for cricket match entries."""

    __tablename__ = "cricket_match_entries"

    # Set the entry type
    entry_type: Mapped[EntryType] = mapped_column(
        SA_Enum(EntryType),
        default=EntryType.CRICKET_MATCH,
        index=True,
    )

    # Match details (match DB schema)
    match_format: Mapped[MatchFormat | None] = mapped_column(SA_Enum(MatchFormat))
    opposition_team: Mapped[str] = mapped_column(String)
    venue: Mapped[str] = mapped_column(String)
    home_away: Mapped[str] = mapped_column(String)
    result: Mapped[str] = mapped_column(String)
    team_name: Mapped[str] = mapped_column(String)

    # Team performance
    team_total: Mapped[int | None] = mapped_column()
    team_wickets: Mapped[int | None] = mapped_column()
    team_overs: Mapped[float | None] = mapped_column()
    opposition_total: Mapped[int | None] = mapped_column()
    opposition_wickets: Mapped[int | None] = mapped_column()
    opposition_overs: Mapped[float | None] = mapped_column()

    # Personal batting performance
    batting_position: Mapped[int | None] = mapped_column()
    runs_scored: Mapped[int | None] = mapped_column()
    balls_faced: Mapped[int | None] = mapped_column()
    boundaries: Mapped[int | None] = mapped_column()
    sixes: Mapped[int | None] = mapped_column()
    dismissal_type: Mapped[str | None] = mapped_column(String)
    strike_rate: Mapped[float | None] = mapped_column()

    # Personal bowling performance
    overs_bowled: Mapped[float | None] = mapped_column()
    runs_conceded: Mapped[int | None] = mapped_column()
    wickets_taken: Mapped[int | None] = mapped_column()
    economy_rate: Mapped[float | None] = mapped_column()
    best_bowling: Mapped[str | None] = mapped_column(String)

    # Personal fielding performance
    catches_taken: Mapped[int | None] = mapped_column()
    run_outs: Mapped[int | None] = mapped_column()
    stumpings: Mapped[int | None] = mapped_column()
    fielding_position: Mapped[str | None] = mapped_column(String)

    # Match conditions
    weather_conditions: Mapped[str | None] = mapped_column(String)
    pitch_conditions: Mapped[str | None] = mapped_column(String)
    toss_won_by: Mapped[str | None] = mapped_column(String)
    elected_to: Mapped[str | None] = mapped_column(String)

    # Performance ratings
    batting_performance: Mapped[int | None] = mapped_column()
    bowling_performance: Mapped[int | None] = mapped_column()
    fielding_performance: Mapped[int | None] = mapped_column()
    overall_performance: Mapped[int | None] = mapped_column()

    # Key moments and learnings
    key_moments: Mapped[list[str] | None] = mapped_column(JSON)
    what_went_well: Mapped[list[str] | None] = mapped_column(JSON)
    areas_for_improvement: Mapped[list[str] | None] = mapped_column(JSON)
    captain_feedback: Mapped[str | None] = mapped_column(String)
    coach_feedback: Mapped[str | None] = mapped_column(String)

    # Match logistics
    match_duration_hours: Mapped[float | None] = mapped_column()
    start_time: Mapped[time | None] = mapped_column()
    end_time: Mapped[time | None] = mapped_column()
    match_fee: Mapped[float | None] = mapped_column()
    travel_distance_km: Mapped[float | None] = mapped_column()
