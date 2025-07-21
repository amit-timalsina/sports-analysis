from enum import Enum


class CricketDiscipline(str, Enum):
    """Cricket disciplines."""

    BATTING = "batting"
    BOWLING = "bowling"
    FIELDING = "fielding"
    WICKET_KEEPING = "wicket_keeping"
    ALL_ROUND = "all_round"
