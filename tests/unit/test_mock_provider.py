"""Tests for mock provider."""

import pytest
from conduit.errors import ValidationError
from conduit.providers.mock import MockModel
from conduit.schema.messages import Message
from conduit.schema.options import ChatOptions


@pytest.mark.asyncio
async def test_mock_chat():
    """Test mock chat."""
    model = MockModel(response_content="Hello, world!")
    response = await model.chat([
        Message(role="user", content="Hi")
    ])
    
    assert response.extract_content() == "Hello, world!"
    assert model.call_count == 1
    assert model.last_messages is not None
    assert len(model.last_messages) == 1


@pytest.mark.asyncio
async def test_mock_chat_with_options():
    """Test mock chat with options."""
    model = MockModel(response_content="Response")
    options = ChatOptions(temperature=0.7)
    response = await model.chat([
        Message(role="user", content="Test")
    ], options=options)
    
    assert response.extract_content() == "Response"
    assert model.last_options == options


@pytest.mark.asyncio
async def test_mock_streaming():
    """Test mock streaming."""
    model = MockModel(response_content="Hello")
    chunks = []
    async for event in model.stream([
        Message(role="user", content="Say hello")
    ]):
        chunks.append(event)
    
    assert len(chunks) == 5  # "Hello" has 5 characters
    assert all(chunk["type"] == "content_delta" for chunk in chunks)
    assert "".join(chunk["text"] for chunk in chunks) == "Hello"


@pytest.mark.asyncio
async def test_mock_error():
    """Test mock with error."""
    error = ValidationError("Test error")
    model = MockModel(error=error)
    
    with pytest.raises(ValidationError):
        await model.chat([Message(role="user", content="Test")])


@pytest.mark.asyncio
async def test_mock_delay():
    """Test mock with delay."""
    import time
    model = MockModel(response_content="Delayed", delay=0.1)
    
    start = time.time()
    response = await model.chat([Message(role="user", content="Test")])
    elapsed = time.time() - start
    
    assert response.extract_content() == "Delayed"
    assert elapsed >= 0.1


def test_mock_model_info():
    """Test mock model info."""
    model = MockModel(model="test-model")
    info = model.model_info()
    
    assert info.provider == "mock"
    assert info.model == "test-model"
    assert info.capabilities.streaming is True
    assert info.capabilities.tool_calling is True
