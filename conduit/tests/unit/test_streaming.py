"""Tests for streaming utilities."""

import pytest

from conduit.schema.responses import Response, Usage
from conduit.streaming import collect_stream, stream_to_string, stream_with_callback


@pytest.mark.asyncio
async def test_collect_stream():
    """Test collect_stream assembles stream into Response."""
    events = [
        {"type": "content_delta", "text": "Hello"},
        {"type": "content_delta", "text": " "},
        {"type": "content_delta", "text": "world"},
        {"type": "model", "model": "test-model"},
        {"type": "usage", "usage": {"input_tokens": 5, "output_tokens": 2}},
    ]

    async def event_stream():
        for event in events:
            yield event

    response = await collect_stream(event_stream())

    assert isinstance(response, Response)
    assert response.extract_content() == "Hello world"
    assert response.model == "test-model"
    assert response.usage.input_tokens == 5
    assert response.usage.output_tokens == 2


@pytest.mark.asyncio
async def test_stream_to_string():
    """Test stream_to_string collects content."""
    events = [
        {"type": "content_delta", "text": "Hello"},
        {"type": "content_delta", "text": " "},
        {"type": "content_delta", "text": "world"},
    ]

    async def event_stream():
        for event in events:
            yield event

    content = await stream_to_string(event_stream())
    assert content == "Hello world"


@pytest.mark.asyncio
async def test_stream_with_callback():
    """Test stream_with_callback calls callback for each event."""
    events = [
        {"type": "content_delta", "text": "Hello"},
        {"type": "content_delta", "text": " world"},
    ]

    async def event_stream():
        for event in events:
            yield event

    callback_events = []

    def callback(event):
        callback_events.append(event)

    response = await stream_with_callback(event_stream(), callback)

    assert len(callback_events) == 2
    assert callback_events[0]["type"] == "content_delta"
    assert response.extract_content() == "Hello world"


@pytest.mark.asyncio
async def test_collect_stream_empty():
    """Test collect_stream handles empty stream."""
    async def event_stream():
        if False:
            yield  # Make it an async generator

    response = await collect_stream(event_stream())
    assert isinstance(response, Response)
    assert response.extract_content() == ""


@pytest.mark.asyncio
async def test_collect_stream_with_stop_reason():
    """Test collect_stream captures stop_reason."""
    events = [
        {"type": "content_delta", "text": "Hello"},
        {"type": "stop_reason", "reason": "end_turn"},
    ]

    async def event_stream():
        for event in events:
            yield event

    response = await collect_stream(event_stream())
    assert response.stop_reason == "end_turn"
