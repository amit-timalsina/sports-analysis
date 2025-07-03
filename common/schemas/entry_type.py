from enum import Enum


class EntryType(str, Enum):
    """Types of entries in the system."""

    FITNESS = "FITNESS"
    CRICKET_COACHING = "CRICKET_COACHING"
    CRICKET_MATCH = "CRICKET_MATCH"
    REST_DAY = "REST_DAY"
