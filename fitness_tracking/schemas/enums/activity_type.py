from enum import Enum


class ActivityType(str, Enum):
    """Activity type."""

    CRICKET_MATCH = "CRICKET_MATCH"
    CRICKET_COACHING = "CRICKET_COACHING"
    REST_DAY = "REST_DAY"
    FITNESS = "FITNESS"
