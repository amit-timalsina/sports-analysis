"""Fitness tracking FastAPI routers."""

from .activity_router import (
    cricket_coaching_router,
    cricket_match_router,
    fitness_router,
    rest_day_router,
)

__all__ = (
    "cricket_coaching_router",
    "cricket_match_router",
    "fitness_router",
    "rest_day_router",
)
