from enum import Enum


class RestType(str, Enum):
    """Rest day types."""

    COMPLETE = "complete"
    ACTIVE = "active"
    PARTIAL = "partial"
    FORCED = "forced"
    SCHEDULED = "scheduled"
    RECOVERY_DAY = "recovery_day"
