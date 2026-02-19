"""
Tests for cache management functionality.
"""

from datetime import UTC, datetime, timedelta
from time import sleep

import pytest

from src.cache import CachedData, CacheManager


class TestCachedData:
    """Tests for CachedData class."""

    def test_is_expired_false(self):
        """Test is_expired returns False for fresh data."""
        cached = CachedData(data="test", cached_at=datetime.now(UTC), ttl=60)
        assert cached.is_expired() is False

    def test_is_expired_true(self):
        """Test is_expired returns True for expired data."""
        # Create data that expired 1 second ago
        cached = CachedData(
            data="test", cached_at=datetime.now(UTC) - timedelta(seconds=61), ttl=60
        )
        assert cached.is_expired() is True

    def test_age_seconds(self):
        """Test age_seconds returns correct age."""
        # Create data from 5 seconds ago
        cached = CachedData(data="test", cached_at=datetime.now(UTC) - timedelta(seconds=5), ttl=60)
        age = cached.age_seconds()
        # Allow small margin for test execution time
        assert 4.5 <= age <= 5.5

    def test_remaining_ttl_positive(self):
        """Test remaining_ttl returns positive value for fresh data."""
        cached = CachedData(
            data="test", cached_at=datetime.now(UTC) - timedelta(seconds=10), ttl=60
        )
        remaining = cached.remaining_ttl()
        # Should have about 50 seconds remaining
        assert 49 <= remaining <= 51

    def test_remaining_ttl_negative(self):
        """Test remaining_ttl returns negative value for expired data."""
        cached = CachedData(
            data="test", cached_at=datetime.now(UTC) - timedelta(seconds=70), ttl=60
        )
        remaining = cached.remaining_ttl()
        # Should be about -10 seconds
        assert -11 <= remaining <= -9


class TestCacheManager:
    """Tests for CacheManager class."""

    @pytest.fixture
    def cache_manager(self):
        """Create a fresh CacheManager for each test."""
        return CacheManager()

    def test_cache_miss(self, cache_manager):
        """Test cache miss increments stats."""
        result = cache_manager.get("nonexistent")
        assert result is None

        stats = cache_manager.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0

    def test_cache_hit(self, cache_manager):
        """Test cache hit returns data and increments stats."""
        cache_manager.set("test_key", "test_value", ttl=60)
        result = cache_manager.get("test_key")

        assert result == "test_value"

        stats = cache_manager.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

    def test_cache_expiration(self, cache_manager):
        """Test expired data is removed and expiration is tracked."""
        # Set data with 1 second TTL
        cache_manager.set("expiring_key", "value", ttl=1)

        # Wait for expiration
        sleep(1.1)

        result = cache_manager.get("expiring_key")
        assert result is None

        stats = cache_manager.get_stats()
        assert stats["expirations"] == 1

    def test_set_overwrites_existing(self, cache_manager):
        """Test setting same key overwrites previous value."""
        cache_manager.set("key", "value1", ttl=60)
        cache_manager.set("key", "value2", ttl=60)

        result = cache_manager.get("key")
        assert result == "value2"

    def test_invalidate_existing_key(self, cache_manager):
        """Test invalidate removes existing key and returns True."""
        cache_manager.set("key", "value", ttl=60)

        result = cache_manager.invalidate("key")
        assert result is True

        # Key should no longer exist
        assert cache_manager.get("key") is None

    def test_invalidate_nonexistent_key(self, cache_manager):
        """Test invalidate returns False for nonexistent key."""
        result = cache_manager.invalidate("nonexistent")
        assert result is False

    def test_clear(self, cache_manager):
        """Test clear removes all entries."""
        cache_manager.set("key1", "value1", ttl=60)
        cache_manager.set("key2", "value2", ttl=60)
        cache_manager.set("key3", "value3", ttl=60)

        cache_manager.clear()

        stats = cache_manager.get_stats()
        assert stats["current_size"] == 0
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None
        assert cache_manager.get("key3") is None

    def test_get_stats_with_no_requests(self, cache_manager):
        """Test get_stats with no cache requests."""
        stats = cache_manager.get_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["expirations"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["current_size"] == 0
        assert stats["entries"] == {}

    def test_get_stats_hit_rate(self, cache_manager):
        """Test get_stats calculates hit rate correctly."""
        cache_manager.set("key", "value", ttl=60)

        # 1 hit
        cache_manager.get("key")
        # 2 misses
        cache_manager.get("nonexistent1")
        cache_manager.get("nonexistent2")

        stats = cache_manager.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["hit_rate"] == pytest.approx(1 / 3)

    def test_get_stats_entries_info(self, cache_manager):
        """Test get_stats includes entry information."""
        cache_manager.set("key1", "value1", ttl=60)
        cache_manager.set("key2", "value2", ttl=30)

        stats = cache_manager.get_stats()

        assert "entries" in stats
        assert "key1" in stats["entries"]
        assert "key2" in stats["entries"]

        entry1 = stats["entries"]["key1"]
        assert "age_seconds" in entry1
        assert "remaining_ttl" in entry1
        assert "is_expired" in entry1
        assert entry1["is_expired"] is False
        assert entry1["remaining_ttl"] > 0

    def test_cleanup_expired_removes_expired(self, cache_manager):
        """Test cleanup_expired removes only expired entries."""
        # Set some entries with different TTLs
        cache_manager.set("fresh", "value", ttl=60)
        cache_manager.set("expiring1", "value", ttl=1)
        cache_manager.set("expiring2", "value", ttl=1)

        # Wait for expiration
        sleep(1.1)

        removed_count = cache_manager.cleanup_expired()

        assert removed_count == 2
        assert cache_manager.get("fresh") == "value"
        assert cache_manager.get("expiring1") is None
        assert cache_manager.get("expiring2") is None

    def test_cleanup_expired_no_expired_entries(self, cache_manager):
        """Test cleanup_expired returns 0 when no entries are expired."""
        cache_manager.set("key1", "value1", ttl=60)
        cache_manager.set("key2", "value2", ttl=60)

        removed_count = cache_manager.cleanup_expired()

        assert removed_count == 0
        stats = cache_manager.get_stats()
        assert stats["current_size"] == 2

    def test_cleanup_expired_empty_cache(self, cache_manager):
        """Test cleanup_expired returns 0 for empty cache."""
        removed_count = cache_manager.cleanup_expired()
        assert removed_count == 0

    def test_cache_with_complex_data(self, cache_manager):
        """Test caching complex data structures."""
        complex_data = {
            "list": [1, 2, 3],
            "nested": {"key": "value"},
            "number": 42,
        }

        cache_manager.set("complex", complex_data, ttl=60)
        result = cache_manager.get("complex")

        assert result == complex_data
        assert result["list"] == [1, 2, 3]
        assert result["nested"]["key"] == "value"
