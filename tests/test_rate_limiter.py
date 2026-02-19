"""Tests for rate limiter functionality."""

import asyncio

import pytest

from src.rate_limiter import RateLimiter


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limiter_basic():
    """Test basic rate limiting functionality."""
    limiter = RateLimiter(max_requests=3, window_seconds=1)

    # First 3 requests should succeed immediately
    start = asyncio.get_event_loop().time()
    await limiter.acquire()
    await limiter.acquire()
    await limiter.acquire()
    elapsed = asyncio.get_event_loop().time() - start

    # Should complete almost instantly
    assert elapsed < 0.1

    # Stats should show 3 active requests
    stats = limiter.get_stats()
    assert stats["active_requests"] == 3
    assert stats["available_tokens"] == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limiter_blocking():
    """Test that rate limiter blocks when limit exceeded."""
    limiter = RateLimiter(max_requests=2, window_seconds=1)

    # First 2 requests succeed
    await limiter.acquire()
    await limiter.acquire()

    # Third request should block and wait
    start = asyncio.get_event_loop().time()
    await limiter.acquire()
    elapsed = asyncio.get_event_loop().time() - start

    # Should have waited approximately 1 second
    assert 0.9 < elapsed < 1.2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limiter_stats():
    """Test rate limiter statistics."""
    limiter = RateLimiter(max_requests=5, window_seconds=2)

    # Make some requests
    await limiter.acquire()
    await limiter.acquire()

    stats = limiter.get_stats()
    assert stats["max_requests"] == 5
    assert stats["window_seconds"] == 2
    assert stats["active_requests"] == 2
    assert stats["available_tokens"] == 3
    assert stats["utilization"] == 0.4  # 2/5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limiter_reset():
    """Test rate limiter reset functionality."""
    limiter = RateLimiter(max_requests=2, window_seconds=10)

    await limiter.acquire()
    await limiter.acquire()

    stats = limiter.get_stats()
    assert stats["active_requests"] == 2

    # Reset should clear all requests
    limiter.reset()

    stats = limiter.get_stats()
    assert stats["active_requests"] == 0
    assert stats["available_tokens"] == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limiter_window_expiry():
    """Test that requests expire after window."""
    limiter = RateLimiter(max_requests=2, window_seconds=1)

    await limiter.acquire()
    await limiter.acquire()

    # Stats should show 2 active
    stats = limiter.get_stats()
    assert stats["active_requests"] == 2

    # Wait for window to expire
    await asyncio.sleep(1.1)

    # Stats should show 0 active (requests expired)
    stats = limiter.get_stats()
    assert stats["active_requests"] == 0
    assert stats["available_tokens"] == 2
