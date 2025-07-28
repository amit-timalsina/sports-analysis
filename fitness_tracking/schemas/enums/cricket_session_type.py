from enum import Enum


class CricketSessionType(str, Enum):
    """Cricket session types."""

    BATTING_DRILLS = "batting_drills"
    WICKET_KEEPING = "wicket_keeping"
    NETTING = "netting"
    PERSONAL_COACHING = "personal_coaching"
    TEAM_PRACTICE = "team_practice"
    OTHER = "other"
