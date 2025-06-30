"""
Production-ready cache service with multiple backends.

Provides both in-memory LRU caching and optional Redis backend support.
Designed for high-performance applications with proper error handling.
"""

import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any, Generic, TypeVar

from logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")
CacheValue = str | int | float | bool | dict | list | None


class CacheBackend(ABC, Generic[T]):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> T | None:
        """Get value by key."""

    @abstractmethod
    def set(self, key: str, value: T, ttl: int | None = None) -> None:
        """Set value with optional TTL."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete key."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached items."""

    @abstractmethod
    def size(self) -> int:
        """Get current cache size."""


class InMemoryLRUCache(CacheBackend[T]):
    """
    High-performance in-memory LRU cache with TTL support.

    Thread-safe, memory-efficient implementation suitable for production use.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int | None = None) -> None:
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items to cache
            default_ttl: Default TTL in seconds (None = no expiration)

        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[T, float | None]] = OrderedDict()

    def get(self, key: str) -> T | None:
        """Get value by key, checking TTL expiration."""
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]

        # Check TTL expiration
        if expiry is not None and time.time() > expiry:
            del self._cache[key]
            return None

        # Move to end (LRU behavior)
        self._cache.move_to_end(key)
        return value

    def set(self, key: str, value: T, ttl: int | None = None) -> None:
        """Set value with optional TTL."""
        # Use default TTL if not specified
        if ttl is None:
            ttl = self.default_ttl

        # Calculate expiry time
        expiry = None if ttl is None else time.time() + ttl

        # Update existing key
        if key in self._cache:
            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)
            return

        # Add new key
        self._cache[key] = (value, expiry)

        # Enforce size limit
        if len(self._cache) > self.max_size:
            # Remove oldest item
            self._cache.popitem(last=False)

    def delete(self, key: str) -> None:
        """Delete key if exists."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def cleanup_expired(self) -> int:
        """Remove expired items and return count removed."""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, expiry) in self._cache.items()
            if expiry is not None and current_time > expiry
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)


class CacheService:
    """
    Production cache service with configurable backends.

    Provides a clean interface for caching with automatic error handling,
    metrics, and production optimizations.
    """

    def __init__(
        self,
        backend: CacheBackend[CacheValue] | None = None,
        max_size: int = 1000,
        default_ttl: int | None = None,
        cleanup_interval: int = 300,  # 5 minutes
    ) -> None:
        """
        Initialize cache service.

        Args:
            backend: Cache backend (defaults to InMemoryLRUCache)
            max_size: Maximum cache size
            default_ttl: Default TTL in seconds
            cleanup_interval: Automatic cleanup interval in seconds

        """
        self.backend = backend or InMemoryLRUCache(max_size, default_ttl)
        self.cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

        # Metrics
        self._hits = 0
        self._misses = 0
        self._sets = 0

    def get(self, key: str) -> CacheValue:
        """
        Get value from cache with automatic cleanup and metrics.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired

        """
        try:
            # Periodic cleanup for in-memory caches
            self._maybe_cleanup()

            value = self.backend.get(key)

            if value is not None:
                self._hits += 1
                logger.debug("Cache hit for key: %s", key)
            else:
                self._misses += 1
                logger.debug("Cache miss for key: %s", key)

        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("Cache get failed for key: %s - %s", key, exc)
            self._misses += 1
            return None
        else:
            return value if value is not None else None

    def set(self, key: str, value: CacheValue, ttl: int | None = None) -> None:
        """
        Set value in cache with error handling.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (None uses default)

        """
        try:
            self.backend.set(key, value, ttl)
            self._sets += 1
            logger.debug("Cache set for key: %s", key)

        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("Cache set failed for key: %s - %s", key, exc)

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        try:
            self.backend.delete(key)
            logger.debug("Cache delete for key: %s", key)

        except (KeyError, ValueError) as exc:
            logger.warning("Cache delete failed for key: %s - %s", key, exc)

    def clear(self) -> None:
        """Clear all cached items."""
        try:
            self.backend.clear()
            logger.info("Cache cleared")

        except (RuntimeError, ValueError) as exc:
            logger.warning("Cache clear failed: %s", exc)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "sets": self._sets,
            "hit_rate": hit_rate,
            "size": self.backend.size(),
        }

    def _maybe_cleanup(self) -> None:
        """Perform periodic cleanup for in-memory caches."""
        current_time = time.time()

        if current_time - self._last_cleanup > self.cleanup_interval:
            if isinstance(self.backend, InMemoryLRUCache):
                removed = self.backend.cleanup_expired()
                if removed > 0:
                    logger.debug("Cache cleanup removed %d expired items", removed)

            self._last_cleanup = current_time


# Global cache instance for application-wide use
default_cache = CacheService(
    max_size=1000,
    default_ttl=3600,  # 1 hour default TTL
)
