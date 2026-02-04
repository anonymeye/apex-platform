"""Tests for error classes."""

from conduit.errors import (
    AuthenticationError,
    ConduitError,
    MaxIterationsError,
    ProviderError,
    RateLimitError,
    TimeoutError,
    ToolExecutionError,
    ValidationError,
)


def test_conduit_error():
    """Test base error."""
    error = ConduitError("test error")
    assert str(error) == "test error"
    assert isinstance(error, Exception)


def test_provider_error():
    """Test provider error with metadata."""
    error = ProviderError("API error", provider="openai", status_code=500)
    assert error.provider == "openai"
    assert error.status_code == 500
    assert str(error) == "API error"


def test_authentication_error():
    """Test authentication error."""
    error = AuthenticationError("Invalid key", provider="openai")
    assert isinstance(error, ProviderError)
    assert error.provider == "openai"


def test_rate_limit_error():
    """Test rate limit error with retry_after."""
    error = RateLimitError("Rate limited", retry_after=60.0, provider="openai")
    assert error.retry_after == 60.0
    assert error.provider == "openai"
    assert isinstance(error, ProviderError)


def test_validation_error():
    """Test validation error."""
    error = ValidationError("Invalid data")
    assert isinstance(error, ConduitError)
    assert str(error) == "Invalid data"


def test_timeout_error():
    """Test timeout error."""
    error = TimeoutError("Request timed out")
    assert isinstance(error, ConduitError)
    assert str(error) == "Request timed out"


def test_max_iterations_error():
    """Test max iterations error."""
    error = MaxIterationsError("Exceeded max iterations")
    assert isinstance(error, ConduitError)
    assert str(error) == "Exceeded max iterations"


def test_tool_execution_error():
    """Test tool execution error."""
    error = ToolExecutionError("Tool failed", tool_name="calculator")
    assert isinstance(error, ConduitError)
    assert error.tool_name == "calculator"
    assert str(error) == "Tool failed"
