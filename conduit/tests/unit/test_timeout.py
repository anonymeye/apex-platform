"""Tests for timeout interceptor."""

import asyncio

import pytest
from conduit.errors import TimeoutError
from conduit.interceptors import execute_interceptors
from conduit.interceptors.timeout import TimeoutInterceptor
from conduit.providers.mock import MockModel
from conduit.schema.messages import Message


@pytest.mark.asyncio
async def test_timeout_successful_request():
    """Test timeout interceptor with successful request."""
    model = MockModel(response_content="Success", delay=0.01)
    messages = [Message(role="user", content="Test")]
    interceptor = TimeoutInterceptor(timeout_seconds=1.0)
    
    response = await execute_interceptors(model, messages, [interceptor])
    
    assert response.extract_content() == "Success"


@pytest.mark.asyncio
async def test_timeout_expired():
    """Test timeout interceptor when request times out."""
    # Create a model that takes longer than timeout
    class SlowModel(MockModel):
        async def chat(self, messages, options=None):
            await asyncio.sleep(0.2)  # Longer than timeout
            return await super().chat(messages, options)
    
    model = SlowModel(response_content="Should not reach here")
    messages = [Message(role="user", content="Test")]
    interceptor = TimeoutInterceptor(timeout_seconds=0.1)
    
    with pytest.raises(TimeoutError) as exc_info:
        await execute_interceptors(model, messages, [interceptor])
    
    assert "timed out" in str(exc_info.value).lower()
    assert "0.1" in str(exc_info.value)


@pytest.mark.asyncio
async def test_timeout_custom_timeout():
    """Test timeout interceptor with custom timeout."""
    class SlowModel(MockModel):
        async def chat(self, messages, options=None):
            await asyncio.sleep(0.15)
            return await super().chat(messages, options)
    
    model = SlowModel(response_content="Success")
    messages = [Message(role="user", content="Test")]
    interceptor = TimeoutInterceptor(timeout_seconds=0.2)  # Longer timeout
    
    response = await execute_interceptors(model, messages, [interceptor])
    
    assert response.extract_content() == "Success"


@pytest.mark.asyncio
async def test_timeout_with_other_interceptors():
    """Test timeout interceptor works with other interceptors."""
    class SlowModel(MockModel):
        async def chat(self, messages, options=None):
            await asyncio.sleep(0.15)
            return await super().chat(messages, options)
    
    model = SlowModel(response_content="Success")
    messages = [Message(role="user", content="Test")]
    
    # Timeout should be checked even with other interceptors
    from conduit.interceptors.logging import LoggingInterceptor
    interceptors = [
        LoggingInterceptor(log_request=False, log_response=False),
        TimeoutInterceptor(timeout_seconds=0.2)
    ]
    
    response = await execute_interceptors(model, messages, interceptors)
    
    assert response.extract_content() == "Success"
