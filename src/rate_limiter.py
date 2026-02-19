"""
Rate limiting for FPL MCP Server.

Implements token bucket algorithm to prevent API rate limit violations.
"""

import asyncio
from collections import deque
from datetime import UTC, datetime
import logging

logger = logging.getLogger("fpl_rate_limiter")


class RateLimiter:
    """
    Token bucket rate limiter to prevent API abuse.

    Features:
    - Token bucket algorithm for smooth rate limiting
    - Configurable requests per window
    - Automatic token replenishment
    - Blocking when limit exceeded with wait time calculation
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in the time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Acquire permission to make a request.

        Blocks if rate limit would be exceeded, waiting until a token is available.
        """
        while True:
            async with self._lock:
                now = datetime.now(UTC).timestamp()

                # Remove requests outside the current window
                while self.requests and self.requests[0] < now - self.window_seconds:
                    self.requests.popleft()

                # Check if we have capacity
                if len(self.requests) < self.max_requests:
                    # Add current request timestamp and return
                    self.requests.append(now)
                    logger.debug(
                        f"Rate limit check passed: {len(self.requests)}/{self.max_requests} "
                        f"requests in window"
                    )
                    return

                # Calculate wait time
                oldest_request = self.requests[0]
                wait_time = self.window_seconds - (now - oldest_request) + 0.01  # Small buffer

            # Release lock while waiting (lock released when exiting context manager)
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.2f}s before retry...")
                await asyncio.sleep(wait_time)
            # Loop will retry acquisition

    def get_stats(self) -> dict[str, any]:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary with current usage and limits
        """
        now = datetime.now(UTC).timestamp()

        # Count requests in current window
        active_requests = sum(1 for req in self.requests if req >= now - self.window_seconds)

        return {
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "active_requests": active_requests,
            "available_tokens": max(0, self.max_requests - active_requests),
            "utilization": active_requests / self.max_requests if self.max_requests > 0 else 0,
        }

    def reset(self) -> None:
        """Reset rate limiter (clear all request history)."""
        self.requests.clear()
        logger.info("Rate limiter reset")


# Global rate limiter instance
# Conservative default: 100 requests per minute to prevent API bans
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
