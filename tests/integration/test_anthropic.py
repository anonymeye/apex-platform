"""Integration tests for Anthropic provider."""

import pytest
from conduit.errors import AuthenticationError, RateLimitError
from conduit.providers.anthropic import AnthropicModel
from conduit.schema.messages import Message
from conduit.schema.options import ChatOptions


@pytest.mark.asyncio
async def test_anthropic_chat_success(httpx_mock):
    """Test successful Anthropic chat request."""
    httpx_mock.add_response(
        url="https://api.anthropic.com/v1/messages",
        method="POST",
        json={
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Hello! How can I help you?"}],
            "model": "claude-3-5-sonnet-20241022",
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": 10,
                "output_tokens": 7,
            },
        },
    )

    async with AnthropicModel(api_key="test-key", model="claude-3-5-sonnet-20241022") as model:
        response = await model.chat([Message(role="user", content="Hello!")])

        assert response.extract_content() == "Hello! How can I help you?"
        assert response.usage.input_tokens == 10
        assert response.usage.output_tokens == 7
        assert response.model == "claude-3-5-sonnet-20241022"


@pytest.mark.asyncio
async def test_anthropic_chat_with_options(httpx_mock):
    """Test Anthropic chat with options."""
    httpx_mock.add_response(
        url="https://api.anthropic.com/v1/messages",
        method="POST",
        json={
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Response"}],
            "model": "claude-3-5-sonnet-20241022",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 5, "output_tokens": 3},
        },
    )

    async with AnthropicModel(api_key="test-key") as model:
        options = ChatOptions(temperature=0.7, max_tokens=100)
        response = await model.chat([Message(role="user", content="Test")], options=options)

        assert response.extract_content() == "Response"

        # Verify request included options
        request = httpx_mock.get_request()
        assert request is not None
        payload = request.read()
        assert b"temperature" in payload
        assert b"max_tokens" in payload


@pytest.mark.asyncio
async def test_anthropic_streaming(httpx_mock):
    """Test Anthropic streaming."""
    httpx_mock.add_response(
        url="https://api.anthropic.com/v1/messages",
        method="POST",
        status_code=200,
        headers={"Content-Type": "text/event-stream"},
        text='data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}\n\ndata: {"type":"content_block_delta","delta":{"type":"text_delta","text":" world"}}\n\ndata: {"type":"message_stop"}\n\n',
    )

    async with AnthropicModel(api_key="test-key") as model:
        chunks = []
        async for event in model.stream([Message(role="user", content="Say hello")]):
            chunks.append(event)

        # Should have at least some events
        assert len(chunks) > 0


@pytest.mark.asyncio
async def test_anthropic_authentication_error(httpx_mock):
    """Test Anthropic authentication error handling."""
    httpx_mock.add_response(
        url="https://api.anthropic.com/v1/messages",
        method="POST",
        status_code=401,
        json={"error": {"message": "Invalid API key", "type": "authentication_error"}},
    )

    async with AnthropicModel(api_key="invalid-key") as model:
        with pytest.raises(AuthenticationError) as exc_info:
            await model.chat([Message(role="user", content="Test")])

        assert exc_info.value.provider == "anthropic"
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_anthropic_rate_limit_error(httpx_mock):
    """Test Anthropic rate limit error handling."""
    httpx_mock.add_response(
        url="https://api.anthropic.com/v1/messages",
        method="POST",
        status_code=429,
        headers={"retry-after-ms": "60000"},
        json={"error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}},
    )

    async with AnthropicModel(api_key="test-key") as model:
        with pytest.raises(RateLimitError) as exc_info:
            await model.chat([Message(role="user", content="Test")])

        assert exc_info.value.provider == "anthropic"
        assert exc_info.value.retry_after == 60.0


@pytest.mark.asyncio
async def test_anthropic_model_info():
    """Test Anthropic model info."""
    model = AnthropicModel(api_key="test-key", model="claude-3-5-sonnet-20241022")
    info = model.model_info()

    assert info.provider == "anthropic"
    assert info.model == "claude-3-5-sonnet-20241022"
    assert info.capabilities.streaming is True
    assert info.capabilities.tool_calling is True


@pytest.mark.asyncio
async def test_anthropic_tool_calls(httpx_mock):
    """Test Anthropic tool calling."""
    httpx_mock.add_response(
        url="https://api.anthropic.com/v1/messages",
        method="POST",
        json={
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_123",
                    "name": "calculator",
                    "input": {"a": 1, "b": 2},
                }
            ],
            "model": "claude-3-5-sonnet-20241022",
            "stop_reason": "tool_use",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        },
    )

    async with AnthropicModel(api_key="test-key") as model:
        response = await model.chat([Message(role="user", content="Calculate 1+2")])

        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].function.name == "calculator"
        assert response.stop_reason == "tool_use"
