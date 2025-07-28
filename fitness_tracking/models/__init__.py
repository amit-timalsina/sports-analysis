"""Fitness tracking SQLAlchemy 2.0 models."""

# Import all models for SQLAlchemy discovery
from .cricket_coaching import CricketCoachingEntry
from .cricket_match import CricketMatchEntry
from .fitness import FitnessEntry
from .rest_day import RestDayEntry

__all__ = (
    "CricketCoachingEntry",
    "CricketMatchEntry",
    "FitnessEntry",
    "RestDayEntry",
)
