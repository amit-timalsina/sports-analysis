"""Exercise type enum."""

from enum import Enum


class ExerciseType(str, Enum):
    """Types of exercises."""

    CARDIO = "cardio"
    STRENGTH = "strength"
    FLEXIBILITY = "flexibility"
    SPORTS = "sports"
    OTHER = "other"
