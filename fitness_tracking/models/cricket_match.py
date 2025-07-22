"""Cricket activity tracking SQLAlchemy 2.0 models."""

from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy import Enum as SA_Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models.activity import ActivityEntry
from fitness_tracking.schemas.enums.activity_type import ActivityType
from fitness_tracking.schemas.enums.match_format import MatchFormat

if TYPE_CHECKING:
    from voice_processing.models.conversation import Conversation


class CricketMatchEntry(ActivityEntry):
    """Model for cricket match entries."""

    __tablename__ = "cricket_match_entries"

    # Set the entry type
    activity_type: Mapped[ActivityType] = mapped_column(
        SA_Enum(ActivityType),
        default=ActivityType.CRICKET_MATCH,
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

    # relationship to conversation
    conversation: Mapped["Conversation"] = relationship(
        back_populates="activity_entries",
    )
