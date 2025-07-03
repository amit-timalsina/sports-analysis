"""Intensity level enum."""

from enum import Enum


class IntensityLevel(str, Enum):
    """Exercise intensity levels."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
