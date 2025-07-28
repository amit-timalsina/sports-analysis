"""Fitness tracking Pydantic schemas."""

from .cricket_coaching import (
    CricketCoachingEntryCreate,
    CricketCoachingEntryRead,
    CricketCoachingEntryUpdate,
)
from .cricket_match import CricketMatchEntryCreate, CricketMatchEntryRead, CricketMatchEntryUpdate
from .fitness import (
    FitnessEntryCreate,
    FitnessEntryRead,
    FitnessEntryUpdate,
)
from .rest_day import RestDayEntryCreate, RestDayEntryRead, RestDayEntryUpdate

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
