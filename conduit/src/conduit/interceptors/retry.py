"""Retry interceptor for handling transient failures."""

import asyncio
import random
from dataclasses import dataclass

from conduit.errors import ProviderError, RateLimitError, TimeoutError
from conduit.interceptors.context import Context


@dataclass
class RetryInterceptor:
    """Retry failed requests with exponential backoff.

    This interceptor automatically retries failed requests for retryable errors
    (rate limits, timeouts, server errors) with exponential backoff and jitter.

    Attributes:
        max_attempts: Maximum number of attempts (including initial)
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        multiplier: Multiplier for exponential backoff
        jitter: Jitter factor (0.0 to 1.0) to add randomness

    Examples:
        >>> interceptor = RetryInterceptor(max_attempts=3)
        >>> response = await execute_interceptors(
        ...     model, messages, [interceptor]
        ... )
    """

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: float = 0.1

    async def enter(self, ctx: Context) -> Context:
        """Initialize retry metadata."""
        if "retry_attempt" not in ctx.metadata:
            ctx.metadata["retry_attempt"] = 0
        return ctx

    async def error(self, ctx: Context, error: Exception) -> Context:
        """Handle errors with retry logic."""
        attempt = ctx.metadata.get("retry_attempt", 0)

        # Check if error is retryable
        if not self._is_retryable(error):
            return ctx

        # Keep retrying until we succeed or run out of attempts
        while attempt < self.max_attempts - 1:
            # Calculate delay with exponential backoff and jitter
            delay = min(self.initial_delay * (self.multiplier**attempt), self.max_delay)

            # Add jitter
            if self.jitter > 0:
                jitter_amount = delay * self.jitter
                delay += random.uniform(-jitter_amount, jitter_amount)
                delay = max(0.0, delay)  # Ensure non-negative

            # Wait before retry
            await asyncio.sleep(delay)

            # Increment attempt counter
            attempt += 1
            ctx.metadata["retry_attempt"] = attempt

            # Retry the model call
            try:
                ctx.response = await ctx.model.chat(ctx.get_messages(), ctx.get_opts())
                # Success! Clear error and return
                ctx.error = None
                return ctx
            except Exception as e:
                # Check if this new error is retryable
                if not self._is_retryable(e):
                    ctx.error = e
                    return ctx
                # Continue retry loop with new error
                error = e

        # Out of attempts, keep the error
        return ctx

    def _is_retryable(self, error: Exception) -> bool:
        """Check if error is retryable.

        Args:
            error: Exception to check

        Returns:
            True if error is retryable, False otherwise
        """
        if isinstance(error, RateLimitError | TimeoutError):
            return True

        # Check for server errors (5xx status codes)
        if isinstance(error, ProviderError):
            if error.status_code is not None:
                return 500 <= error.status_code < 600

        return False
