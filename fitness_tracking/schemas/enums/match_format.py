from enum import Enum


class MatchFormat(str, Enum):
    """Cricket match formats."""

    T20 = "t20"
    ODI = "odi"
    TEST = "test"
    LIST_A = "list_a"
    FIRST_CLASS = "first_class"
    FRIENDLY = "friendly"
    PRACTICE_MATCH = "practice_match"
