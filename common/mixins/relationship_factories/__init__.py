"""
Often we end up with same relationship in multiple places.

This module exposes factories for creating relationship mixins.
These mixins can then be used to add relationships to models. The greatest benefit is that
the relationship is only defined once, so it is easier to maintain and there is consistency.

"""

from .user_relationship_factory import user_relationship_factory

__all__ = ("user_relationship_factory",)
