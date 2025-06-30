"""Fitness tracking models."""

# Import all models for SQLAlchemy discovery
from .cricket import (
    CricketCoachingEntry,
    CricketMatchEntry,
    CricketSessionType,
    MatchType,
    RestDayEntry,
    RestType,
)
from .fitness import FitnessEntry, FitnessType, Intensity

__all__ = (
    "CricketCoachingEntry",
    "CricketMatchEntry",
    "CricketSessionType",
    "FitnessEntry",
    "FitnessType",
    "Intensity",
    "MatchType",
    "RestDayEntry",
    "RestType",
)
