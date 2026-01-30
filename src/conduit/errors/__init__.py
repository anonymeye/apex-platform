"""Error classes for Conduit."""

from conduit.errors.base import (
    AuthenticationError,
    ConduitError,
    MaxIterationsError,
    ProviderError,
    RateLimitError,
    TimeoutError,
    ToolExecutionError,
    ValidationError,
)

__all__ = [
    "ConduitError",
    "ProviderError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "TimeoutError",
    "MaxIterationsError",
    "ToolExecutionError",
]
