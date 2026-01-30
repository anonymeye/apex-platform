"""Rate limit interceptor for request throttling."""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field

from conduit.interceptors.context import Context


@dataclass
class RateLimitInterceptor:
    """Rate limit requests using token bucket algorithm.

    This interceptor implements a token bucket rate limiter to ensure
    requests don't exceed specified rate limits. It will wait if necessary
    to stay within limits.

    Attributes:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds for rate limit
        tokens: Current number of available tokens
        last_refill: Timestamp of last token refill
        request_times: Deque of request timestamps for sliding window

    Examples:
        >>> # Allow 10 requests per minute
        >>> interceptor = RateLimitInterceptor(max_requests=10, window_seconds=60)
        >>> response = await execute_interceptors(
        ...     model, messages, [interceptor]
        ... )
    """

    max_requests: int = 10
    window_seconds: float = 60.0
    tokens: int = field(default=0, init=False)
    last_refill: float = field(default_factory=time.time, init=False)
    request_times: deque[float] = field(default_factory=deque, init=False)

    def __post_init__(self) -> None:
        """Initialize tokens to max_requests."""
        self.tokens = self.max_requests

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill

        if elapsed >= self.window_seconds:
            # Full refill
            self.tokens = self.max_requests
            self.last_refill = now
            self.request_times.clear()
        else:
            # Partial refill based on elapsed time
            tokens_to_add = int((elapsed / self.window_seconds) * self.max_requests)
            if tokens_to_add > 0:
                self.tokens = min(self.tokens + tokens_to_add, self.max_requests)
                self.last_refill = now

        # Clean up old request times outside the window
        cutoff = now - self.window_seconds
        while self.request_times and self.request_times[0] < cutoff:
            self.request_times.popleft()

    async def enter(self, ctx: Context) -> Context:
        """Check rate limit and wait if necessary."""
        self._refill_tokens()

        # Check if we have tokens available
        if self.tokens <= 0:
            # Calculate wait time
            if self.request_times:
                oldest_request = self.request_times[0]
                wait_time = self.window_seconds - (time.time() - oldest_request)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    self._refill_tokens()

        # Check again after waiting
        if self.tokens <= 0:
            # Still no tokens, wait for next window
            await asyncio.sleep(self.window_seconds)
            self._refill_tokens()

        # Consume a token
        self.tokens -= 1
        self.request_times.append(time.time())

        return ctx
