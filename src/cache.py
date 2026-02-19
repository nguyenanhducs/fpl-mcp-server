"""
Cache management for FPL MCP Server.

Provides TTL-aware caching with automatic expiration and cache statistics.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from typing import Any

logger = logging.getLogger("fpl_cache")


@dataclass
class CachedData[T]:
    """Container for cached data with metadata."""

    data: T
    cached_at: datetime
    ttl: int  # Time to live in seconds

    def is_expired(self) -> bool:
        """Check if cached data has expired."""
        age = (datetime.now(UTC) - self.cached_at).total_seconds()
        return age >= self.ttl

    def age_seconds(self) -> float:
        """Get age of cached data in seconds."""
        return (datetime.now(UTC) - self.cached_at).total_seconds()

    def remaining_ttl(self) -> float:
        """Get remaining TTL in seconds (can be negative if expired)."""
        return self.ttl - self.age_seconds()


class CacheManager:
    """
    Manages cached data with TTL enforcement and statistics.

    Features:
    - Automatic expiration based on TTL
    - Cache hit/miss statistics
    - Support for custom TTL per cache entry
    """

    def __init__(self):
        self._cache: dict[str, CachedData] = {}
        self._stats = {"hits": 0, "misses": 0, "expirations": 0}

    def get(self, key: str) -> Any | None:
        """
        Get data from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached data if valid, None if expired or missing
        """
        if key not in self._cache:
            self._stats["misses"] += 1
            logger.debug(f"Cache miss: {key}")
            return None

        cached = self._cache[key]

        if cached.is_expired():
            self._stats["expirations"] += 1
            logger.info(
                f"Cache expired: {key} (age: {cached.age_seconds():.1f}s, ttl: {cached.ttl}s)"
            )
            del self._cache[key]
            return None

        self._stats["hits"] += 1
        logger.debug(
            f"Cache hit: {key} (age: {cached.age_seconds():.1f}s, "
            f"remaining: {cached.remaining_ttl():.1f}s)"
        )
        return cached.data

    def set(self, key: str, data: Any, ttl: int) -> None:
        """
        Store data in cache with TTL.

        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds
        """
        self._cache[key] = CachedData(data=data, cached_at=datetime.now(UTC), ttl=ttl)
        logger.debug(f"Cache set: {key} (ttl: {ttl}s)")

    def invalidate(self, key: str) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if key was cached, False otherwise
        """
        if key in self._cache:
            del self._cache[key]
            logger.info(f"Cache invalidated: {key}")
            return True
        return False

    def clear(self) -> None:
        """Clear all cached data."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared: {count} entries removed")

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with hits, misses, expirations, hit_rate, and current size
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0

        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "expirations": self._stats["expirations"],
            "hit_rate": hit_rate,
            "current_size": len(self._cache),
            "entries": {
                key: {
                    "age_seconds": cached.age_seconds(),
                    "remaining_ttl": cached.remaining_ttl(),
                    "is_expired": cached.is_expired(),
                }
                for key, cached in self._cache.items()
            },
        }

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        expired_keys = [key for key, cached in self._cache.items() if cached.is_expired()]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)


# Global cache manager instance
cache_manager = CacheManager()
