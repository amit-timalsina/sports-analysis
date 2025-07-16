"""Database models for auth."""

from .user import User
from .user_identity import UserIdentity

__all__ = (
    "User",
    "UserIdentity",
)
