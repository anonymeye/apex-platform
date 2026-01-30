"""Tests for logging interceptor."""

import logging

import pytest
from conduit.errors import ValidationError
from conduit.interceptors import execute_interceptors
from conduit.interceptors.logging import LoggingInterceptor
from conduit.providers.mock import MockModel
from conduit.schema.messages import Message


@pytest.mark.asyncio
async def test_logging_interceptor_basic(caplog):
    """Test basic logging interceptor."""
    caplog.set_level(logging.INFO)
    
    model = MockModel(response_content="Test response")
    messages = [Message(role="user", content="Test")]
    interceptor = LoggingInterceptor()
    
    response = await execute_interceptors(model, messages, [interceptor])
    
    assert response.extract_content() == "Test response"
    # Check that logs were created
    assert len(caplog.records) > 0


@pytest.mark.asyncio
async def test_logging_interceptor_with_custom_logger(caplog):
    """Test logging interceptor with custom logger."""
    custom_logger = logging.getLogger("custom")
    custom_logger.setLevel(logging.DEBUG)
    
    model = MockModel(response_content="Test")
    messages = [Message(role="user", content="Test")]
    interceptor = LoggingInterceptor(logger=custom_logger, log_level=logging.DEBUG)
    
    response = await execute_interceptors(model, messages, [interceptor])
    
    assert response.extract_content() == "Test"


@pytest.mark.asyncio
async def test_logging_interceptor_error_logging(caplog):
    """Test logging interceptor logs errors."""
    caplog.set_level(logging.ERROR)
    
    error = ValidationError("Test error")
    model = MockModel(error=error)
    messages = [Message(role="user", content="Test")]
    interceptor = LoggingInterceptor(log_errors=True)
    
    with pytest.raises(ValidationError):
        await execute_interceptors(model, messages, [interceptor])
    
    # Should have logged the error
    assert len(caplog.records) > 0


@pytest.mark.asyncio
async def test_logging_interceptor_disable_logging(caplog):
    """Test logging interceptor can be disabled."""
    model = MockModel(response_content="Test")
    messages = [Message(role="user", content="Test")]
    interceptor = LoggingInterceptor(
        log_request=False,
        log_response=False,
        log_errors=False
    )
    
    response = await execute_interceptors(model, messages, [interceptor])
    
    assert response.extract_content() == "Test"
    # Should not log anything
    assert len(caplog.records) == 0
