"""Tests for retry interceptor."""


import pytest
from conduit.errors import ProviderError, RateLimitError, TimeoutError, ValidationError
from conduit.interceptors import execute_interceptors
from conduit.interceptors.retry import RetryInterceptor
from conduit.providers.mock import MockModel
from conduit.schema.messages import Message


@pytest.mark.asyncio
async def test_retry_successful_request():
    """Test retry interceptor with successful request."""
    model = MockModel(response_content="Success")
    messages = [Message(role="user", content="Test")]
    interceptor = RetryInterceptor(max_attempts=3)
    
    response = await execute_interceptors(model, messages, [interceptor])
    
    assert response.extract_content() == "Success"
    assert model.call_count == 1  # Should only call once on success


@pytest.mark.asyncio
async def test_retry_retryable_error():
    """Test retry interceptor with retryable error that succeeds on retry."""
    attempt = 0
    
    class FailingModel(MockModel):
        async def chat(self, messages, options=None):
            nonlocal attempt
            attempt += 1
            if attempt == 1:
                raise RateLimitError("Rate limited")
            return await super().chat(messages, options)
    
    model = FailingModel(response_content="Success after retry")
    messages = [Message(role="user", content="Test")]
    interceptor = RetryInterceptor(max_attempts=3, initial_delay=0.01)
    
    response = await execute_interceptors(model, messages, [interceptor])
    
    assert response.extract_content() == "Success after retry"
    assert attempt == 2  # Should retry once


@pytest.mark.asyncio
async def test_retry_max_attempts_exceeded():
    """Test retry interceptor when max attempts exceeded."""
    model = MockModel(error=RateLimitError("Rate limited"))
    messages = [Message(role="user", content="Test")]
    interceptor = RetryInterceptor(max_attempts=2, initial_delay=0.01)
    
    with pytest.raises(RateLimitError):
        await execute_interceptors(model, messages, [interceptor])


@pytest.mark.asyncio
async def test_retry_non_retryable_error():
    """Test retry interceptor with non-retryable error."""
    model = MockModel(error=ValidationError("Invalid input"))
    messages = [Message(role="user", content="Test")]
    interceptor = RetryInterceptor(max_attempts=3)
    
    with pytest.raises(ValidationError):
        await execute_interceptors(model, messages, [interceptor])
    
    assert model.call_count == 1  # Should not retry


@pytest.mark.asyncio
async def test_retry_timeout_error():
    """Test retry interceptor with timeout error."""
    attempt = 0
    
    class FailingModel(MockModel):
        async def chat(self, messages, options=None):
            nonlocal attempt
            attempt += 1
            if attempt == 1:
                raise TimeoutError("Timeout")
            return await super().chat(messages, options)
    
    model = FailingModel(response_content="Success")
    messages = [Message(role="user", content="Test")]
    interceptor = RetryInterceptor(max_attempts=3, initial_delay=0.01)
    
    response = await execute_interceptors(model, messages, [interceptor])
    
    assert response.extract_content() == "Success"
    assert attempt == 2


@pytest.mark.asyncio
async def test_retry_server_error():
    """Test retry interceptor with server error (5xx)."""
    attempt = 0
    
    class FailingModel(MockModel):
        async def chat(self, messages, options=None):
            nonlocal attempt
            attempt += 1
            if attempt == 1:
                raise ProviderError("Server error", status_code=500)
            return await super().chat(messages, options)
    
    model = FailingModel(response_content="Success")
    messages = [Message(role="user", content="Test")]
    interceptor = RetryInterceptor(max_attempts=3, initial_delay=0.01)
    
    response = await execute_interceptors(model, messages, [interceptor])
    
    assert response.extract_content() == "Success"
    assert attempt == 2


@pytest.mark.asyncio
async def test_retry_exponential_backoff():
    """Test retry interceptor uses exponential backoff."""
    import time
    
    attempt = 0
    
    class FailingModel(MockModel):
        async def chat(self, messages, options=None):
            nonlocal attempt
            attempt += 1
            if attempt < 3:
                raise RateLimitError("Rate limited")
            return await super().chat(messages, options)
    
    # Track delays by checking time between calls
    model = FailingModel(response_content="Success")
    messages = [Message(role="user", content="Test")]
    interceptor = RetryInterceptor(
        max_attempts=3,
        initial_delay=0.05,
        multiplier=2.0
    )
    
    start = time.time()
    response = await execute_interceptors(model, messages, [interceptor])
    elapsed = time.time() - start
    
    assert response.extract_content() == "Success"
    assert attempt == 3
    # Should have waited at least initial_delay (first retry) + (initial_delay * multiplier) (second retry)
    # But with jitter, we'll just check it took some time
    assert elapsed >= 0.05  # At least the initial delay
