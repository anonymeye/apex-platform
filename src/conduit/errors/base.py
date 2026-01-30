"""Core exception classes for Conduit."""


class ConduitError(Exception):
    """Base exception for all Conduit errors."""

    pass


class ProviderError(ConduitError):
    """Error from LLM provider API."""

    def __init__(
        self, message: str, provider: str | None = None, status_code: int | None = None
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


class AuthenticationError(ProviderError):
    """Authentication failed with provider."""

    pass


class RateLimitError(ProviderError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        provider: str | None = None,
    ) -> None:
        super().__init__(message, provider=provider)
        self.retry_after = retry_after


class ValidationError(ConduitError):
    """Data validation error."""

    pass


class TimeoutError(ConduitError):
    """Request timeout."""

    pass


class MaxIterationsError(ConduitError):
    """Agent exceeded maximum iterations."""

    pass


class ToolExecutionError(ConduitError):
    """Error executing tool."""

    def __init__(self, message: str, tool_name: str) -> None:
        super().__init__(message)
        self.tool_name = tool_name
