"""Tests for cache interceptor."""

import asyncio

import pytest
from conduit.interceptors import execute_interceptors
from conduit.interceptors.cache import CacheInterceptor
from conduit.providers.mock import MockModel
from conduit.schema.messages import Message


@pytest.mark.asyncio
async def test_cache_interceptor_cache_hit():
    """Test cache interceptor returns cached response."""
    model = MockModel(response_content="Cached response")
    messages = [Message(role="user", content="Test")]
    interceptor = CacheInterceptor()
    
    # First call
    response1 = await execute_interceptors(model, messages, [interceptor])
    assert response1.extract_content() == "Cached response"
    assert model.call_count == 1
    
    # Second call should use cache
    response2 = await execute_interceptors(model, messages, [interceptor])
    assert response2.extract_content() == "Cached response"
    assert model.call_count == 1  # Should not call model again


@pytest.mark.asyncio
async def test_cache_interceptor_cache_miss():
    """Test cache interceptor with different messages."""
    model = MockModel(response_content="Response")
    messages1 = [Message(role="user", content="First")]
    messages2 = [Message(role="user", content="Second")]
    interceptor = CacheInterceptor()
    
    # First call
    await execute_interceptors(model, messages1, [interceptor])
    assert model.call_count == 1
    
    # Second call with different messages
    await execute_interceptors(model, messages2, [interceptor])
    assert model.call_count == 2  # Should call model again


@pytest.mark.asyncio
async def test_cache_interceptor_ttl_expiration():
    """Test cache interceptor with TTL expiration."""
    model = MockModel(response_content="Response")
    messages = [Message(role="user", content="Test")]
    interceptor = CacheInterceptor(ttl=0.1)  # Very short TTL
    
    # First call
    await execute_interceptors(model, messages, [interceptor])
    assert model.call_count == 1
    
    # Wait for TTL to expire
    await asyncio.sleep(0.15)
    
    # Second call should not use cache
    await execute_interceptors(model, messages, [interceptor])
    assert model.call_count == 2  # Should call model again


@pytest.mark.asyncio
async def test_cache_interceptor_shared_cache():
    """Test cache interceptor with shared cache."""
    model = MockModel(response_content="Response")
    messages = [Message(role="user", content="Test")]
    
    # Create shared cache
    shared_cache = {}
    interceptor1 = CacheInterceptor(cache=shared_cache)
    interceptor2 = CacheInterceptor(cache=shared_cache)
    
    # First call with interceptor1
    await execute_interceptors(model, messages, [interceptor1])
    assert model.call_count == 1
    
    # Second call with interceptor2 should use shared cache
    await execute_interceptors(model, messages, [interceptor2])
    assert model.call_count == 1  # Should use cache


@pytest.mark.asyncio
async def test_cache_interceptor_custom_key_func():
    """Test cache interceptor with custom key function."""
    def custom_key(messages, opts):
        return "fixed_key"
    
    model = MockModel(response_content="Response")
    messages1 = [Message(role="user", content="First")]
    messages2 = [Message(role="user", content="Second")]
    interceptor = CacheInterceptor(key_func=custom_key)
    
    # First call
    await execute_interceptors(model, messages1, [interceptor])
    assert model.call_count == 1
    
    # Second call with different messages but same key
    await execute_interceptors(model, messages2, [interceptor])
    assert model.call_count == 1  # Should use cache due to fixed key
