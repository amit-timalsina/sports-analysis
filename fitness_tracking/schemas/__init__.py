"""Fitness tracking Pydantic schemas."""

from .cricket import (
    CricketCoachingEntryCreate,
    CricketCoachingEntryRead,
    CricketCoachingEntryUpdate,
    CricketMatchEntryCreate,
    CricketMatchEntryRead,
    CricketMatchEntryUpdate,
)
from .fitness import (
    FitnessEntryCreate,
    FitnessEntryRead,
    FitnessEntryUpdate,
    RestDayEntryCreate,
    RestDayEntryRead,
    RestDayEntryUpdate,
)

__all__ = (
    "CricketCoachingEntryCreate",
    "CricketCoachingEntryRead",
    "CricketCoachingEntryUpdate",
    "CricketMatchEntryCreate",
    "CricketMatchEntryRead",
    "CricketMatchEntryUpdate",
    "FitnessEntryCreate",
    "FitnessEntryRead",
    "FitnessEntryUpdate",
    "RestDayEntryCreate",
    "RestDayEntryRead",
    "RestDayEntryUpdate",
)
