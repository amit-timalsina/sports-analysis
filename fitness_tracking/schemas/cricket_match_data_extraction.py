"""Schema for structured cricket match data extraction from voice input using LLM."""

from pydantic import Field

from common.schemas import AppBaseModel
from fitness_tracking.schemas.enums.match_format import MatchFormat


class CricketMatchDataExtraction(AppBaseModel):
    """Schema for structured cricket match data extraction from voice input."""

    match_format: MatchFormat | None = Field(
        None,
        description="Type of match",
    )
    opposition_team: str | None = Field(None, description="Name of the opposition team")

    venue: str | None = Field(None, description="Match venue")
    home_away: str | None = Field(None, description="Home, away, or neutral venue")
    result: str | None = Field(None, description="Match result (won, lost, draw, no_result)")
    team_name: str | None = Field(None, description="Your team name")

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
