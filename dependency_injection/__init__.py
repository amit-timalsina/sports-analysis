"""Dependency Injection system."""

from .lifespan import lifespan
from .registry import dependencies_registry

__all__ = (
    "dependencies_registry",
    "lifespan",
)
