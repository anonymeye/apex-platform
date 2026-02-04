"""Tests for rate limit interceptor."""

import asyncio
import time

import pytest
from conduit.interceptors import execute_interceptors
from conduit.interceptors.rate_limit import RateLimitInterceptor
from conduit.providers.mock import MockModel
from conduit.schema.messages import Message


@pytest.mark.asyncio
async def test_rate_limit_basic():
    """Test basic rate limiting."""
    model = MockModel(response_content="Test")
    messages = [Message(role="user", content="Test")]
    interceptor = RateLimitInterceptor(max_requests=2, window_seconds=1.0)
    
    # First call
    response1 = await execute_interceptors(model, messages, [interceptor])
    assert response1.extract_content() == "Test"
    
    # Second call (within limit)
    response2 = await execute_interceptors(model, messages, [interceptor])
    assert response2.extract_content() == "Test"
    
    # Third call should wait (rate limited)
    start = time.time()
    response3 = await execute_interceptors(model, messages, [interceptor])
    elapsed = time.time() - start
    
    assert response3.extract_content() == "Test"
    # Should have waited at least part of the window
    assert elapsed >= 0.5  # Rough check


@pytest.mark.asyncio
async def test_rate_limit_token_refill():
    """Test rate limit token refill."""
    model = MockModel(response_content="Test")
    messages = [Message(role="user", content="Test")]
    interceptor = RateLimitInterceptor(max_requests=1, window_seconds=0.1)
    
    # First call
    response1 = await execute_interceptors(model, messages, [interceptor])
    assert response1.extract_content() == "Test"
    
    # Wait for window to pass
    await asyncio.sleep(0.15)
    
    # Second call should not wait (tokens refilled)
    start = time.time()
    response2 = await execute_interceptors(model, messages, [interceptor])
    elapsed = time.time() - start
    
    assert response2.extract_content() == "Test"
    # Should not wait long since tokens were refilled
    assert elapsed < 0.1


@pytest.mark.asyncio
async def test_rate_limit_multiple_requests():
    """Test rate limit with multiple rapid requests."""
    model = MockModel(response_content="Test")
    messages = [Message(role="user", content="Test")]
    interceptor = RateLimitInterceptor(max_requests=3, window_seconds=1.0)
    
    # Make 3 requests rapidly
    responses = []
    for _ in range(3):
        response = await execute_interceptors(model, messages, [interceptor])
        responses.append(response)
    
    assert len(responses) == 3
    assert all(r.extract_content() == "Test" for r in responses)
    
    # Fourth request should wait
    start = time.time()
    response4 = await execute_interceptors(model, messages, [interceptor])
    elapsed = time.time() - start
    
    assert response4.extract_content() == "Test"
    assert elapsed >= 0.5  # Should have waited
