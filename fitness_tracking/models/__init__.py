"""Fitness tracking SQLAlchemy 2.0 models."""

# Import all models for SQLAlchemy discovery
from .cricket import CricketCoachingEntry, CricketMatchEntry
from .fitness import FitnessEntry, RestDayEntry

__all__ = (
    "CricketCoachingEntry",
    "CricketMatchEntry",
    "FitnessEntry",
    "RestDayEntry",
)
