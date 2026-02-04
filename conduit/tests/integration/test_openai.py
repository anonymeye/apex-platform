"""Integration tests for OpenAI provider."""

import pytest
from conduit.errors import AuthenticationError, RateLimitError
from conduit.providers.openai import OpenAIModel
from conduit.schema.messages import Message
from conduit.schema.options import ChatOptions


@pytest.mark.asyncio
async def test_openai_chat_success(httpx_mock):
    """Test successful OpenAI chat request."""
    httpx_mock.add_response(
        url="https://api.openai.com/v1/chat/completions",
        method="POST",
        json={
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you?"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 7,
                "total_tokens": 17
            }
        }
    )
    
    async with OpenAIModel(api_key="test-key", model="gpt-4") as model:
        response = await model.chat([
            Message(role="user", content="Hello!")
        ])
        
        assert response.extract_content() == "Hello! How can I help you?"
        assert response.usage.input_tokens == 10
        assert response.usage.output_tokens == 7
        assert response.model == "gpt-4"


@pytest.mark.asyncio
async def test_openai_chat_with_options(httpx_mock):
    """Test OpenAI chat with options."""
    httpx_mock.add_response(
        url="https://api.openai.com/v1/chat/completions",
        method="POST",
        json={
            "id": "chatcmpl-123",
            "choices": [{
                "message": {"role": "assistant", "content": "Response"},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}
        }
    )
    
    async with OpenAIModel(api_key="test-key") as model:
        options = ChatOptions(temperature=0.7, max_tokens=100)
        response = await model.chat([
            Message(role="user", content="Test")
        ], options=options)
        
        assert response.extract_content() == "Response"
        
        # Verify request included options
        request = httpx_mock.get_request()
        assert request is not None
        payload = request.read()
        assert b"temperature" in payload
        assert b"max_tokens" in payload


@pytest.mark.asyncio
async def test_openai_streaming(httpx_mock):
    """Test OpenAI streaming."""
    # Mock streaming response with proper async stream
    async def stream_response():
        yield b"data: {\"choices\":[{\"delta\":{\"content\":\"Hello\"}}]}\n\n"
        yield b"data: {\"choices\":[{\"delta\":{\"content\":\" world\"}}]}\n\n"
        yield b"data: [DONE]\n\n"
    
    # Use httpx_mock's streaming response
    httpx_mock.add_response(
        url="https://api.openai.com/v1/chat/completions",
        method="POST",
        status_code=200,
        headers={"Content-Type": "text/event-stream"},
        text="data: {\"choices\":[{\"delta\":{\"content\":\"Hello\"}}]}\n\ndata: {\"choices\":[{\"delta\":{\"content\":\" world\"}}]}\n\ndata: [DONE]\n\n"
    )
    
    async with OpenAIModel(api_key="test-key") as model:
        chunks = []
        async for event in model.stream([
            Message(role="user", content="Say hello")
        ]):
            chunks.append(event)
        
        # Should have at least some events
        assert len(chunks) > 0


@pytest.mark.asyncio
async def test_openai_authentication_error(httpx_mock):
    """Test OpenAI authentication error handling."""
    httpx_mock.add_response(
        url="https://api.openai.com/v1/chat/completions",
        method="POST",
        status_code=401,
        json={"error": {"message": "Invalid API key"}}
    )
    
    async with OpenAIModel(api_key="invalid-key") as model:
        with pytest.raises(AuthenticationError) as exc_info:
            await model.chat([Message(role="user", content="Test")])
        
        assert exc_info.value.provider == "openai"
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_openai_rate_limit_error(httpx_mock):
    """Test OpenAI rate limit error handling."""
    httpx_mock.add_response(
        url="https://api.openai.com/v1/chat/completions",
        method="POST",
        status_code=429,
        headers={"retry-after": "60"},
        json={"error": {"message": "Rate limit exceeded"}}
    )
    
    async with OpenAIModel(api_key="test-key") as model:
        with pytest.raises(RateLimitError) as exc_info:
            await model.chat([Message(role="user", content="Test")])
        
        assert exc_info.value.provider == "openai"
        assert exc_info.value.retry_after == 60.0


@pytest.mark.asyncio
async def test_openai_model_info():
    """Test OpenAI model info."""
    model = OpenAIModel(api_key="test-key", model="gpt-4")
    info = model.model_info()
    
    assert info.provider == "openai"
    assert info.model == "gpt-4"
    assert info.capabilities.streaming is True
    assert info.capabilities.tool_calling is True


@pytest.mark.asyncio
async def test_openai_tool_calls(httpx_mock):
    """Test OpenAI tool calling."""
    httpx_mock.add_response(
        url="https://api.openai.com/v1/chat/completions",
        method="POST",
        json={
            "id": "chatcmpl-123",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "calculator",
                            "arguments": "{\"a\": 1, \"b\": 2}"
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        }
    )
    
    async with OpenAIModel(api_key="test-key") as model:
        response = await model.chat([
            Message(role="user", content="Calculate 1+2")
        ])
        
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].function.name == "calculator"
        assert response.stop_reason == "tool_use"
