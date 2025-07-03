"""Cricket related enums."""

from enum import Enum


class CricketDiscipline(str, Enum):
    """Cricket disciplines."""

    BATTING = "batting"
    BOWLING = "bowling"
    FIELDING = "fielding"
    WICKET_KEEPING = "wicket_keeping"
    ALL_ROUND = "all_round"


class MatchFormat(str, Enum):
    """Cricket match formats."""

    T20 = "t20"
    ODI = "odi"
    TEST = "test"
    LIST_A = "list_a"
    FIRST_CLASS = "first_class"
    FRIENDLY = "friendly"
    PRACTICE_MATCH = "practice_match"


class CoachingFocus(str, Enum):
    """Focus areas for coaching sessions."""

    TECHNIQUE = "technique"
    FITNESS = "fitness"
    TACTICS = "tactics"
    MENTAL = "mental"
    SPECIFIC_SKILLS = "specific_skills"
    GAME_SITUATION = "game_situation"


class CricketSessionType(str, Enum):
    """Cricket session types."""

    BATTING_DRILLS = "batting_drills"
    WICKET_KEEPING = "wicket_keeping"
    NETTING = "netting"
    PERSONAL_COACHING = "personal_coaching"
    TEAM_PRACTICE = "team_practice"
    OTHER = "other"


class RestType(str, Enum):
    """Rest day types."""

    COMPLETE = "complete"
    ACTIVE = "active"
    PARTIAL = "partial"
    FORCED = "forced"
    SCHEDULED = "scheduled"
    RECOVERY_DAY = "recovery_day"
