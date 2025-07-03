"""Fitness tracking exceptions."""

from .fitness_errors import (
    CricketCoachingEntryCreationError,
    CricketCoachingEntryNotFoundError,
    CricketMatchEntryCreationError,
    CricketMatchEntryNotFoundError,
    FitnessEntryCreationError,
    FitnessEntryNotFoundError,
    RestDayEntryCreationError,
    RestDayEntryNotFoundError,
)

__all__ = (
    "CricketCoachingEntryCreationError",
    "CricketCoachingEntryNotFoundError",
    "CricketMatchEntryCreationError",
    "CricketMatchEntryNotFoundError",
    "FitnessEntryCreationError",
    "FitnessEntryNotFoundError",
    "RestDayEntryCreationError",
    "RestDayEntryNotFoundError",
)
