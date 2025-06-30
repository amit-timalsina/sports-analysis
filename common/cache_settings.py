from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")


def cached_settings(settings_class: type[T]) -> Callable[[], T]:
    """
    Create a cached getter function for settings classes.

    Parameters
    ----------
    settings_class : type[T]
        The settings class to be instantiated and cached.

    Returns
    -------
    Callable[[], T]
        A cached function that returns an instance of the settings class.

    """
    return lru_cache()(settings_class)
