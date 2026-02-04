"""Tests for schema models."""

import pytest
from conduit.schema.messages import ImageBlock, ImageSource, Message, TextBlock
from conduit.schema.options import ChatOptions
from conduit.schema.responses import FunctionCall, Response, ToolCall, Usage


def test_message_creation():
    """Test creating a simple message."""
    msg = Message(role="user", content="Hello!")
    assert msg.role == "user"
    assert msg.content == "Hello!"
    assert msg.name is None


def test_message_with_text_block():
    """Test message with TextBlock content."""
    msg = Message(
        role="user",
        content=[TextBlock(text="Hello!")]
    )
    assert isinstance(msg.content, list)
    assert len(msg.content) == 1
    assert msg.content[0].text == "Hello!"


def test_message_with_image():
    """Test message with image block."""
    image_source = ImageSource(type="url", url="https://example.com/image.jpg")
    image_block = ImageBlock(source=image_source)
    msg = Message(role="user", content=[image_block])
    assert len(msg.content) == 1
    assert msg.content[0].source.url == "https://example.com/image.jpg"


def test_usage_model():
    """Test Usage model."""
    usage = Usage(input_tokens=10, output_tokens=5)
    assert usage.input_tokens == 10
    assert usage.output_tokens == 5
    assert usage.total_tokens is None


def test_usage_with_total():
    """Test Usage with total_tokens."""
    usage = Usage(input_tokens=10, output_tokens=5, total_tokens=15)
    assert usage.total_tokens == 15


def test_response_extract_content_string():
    """Test Response.extract_content() with string content."""
    response = Response(
        content="Hello, world!",
        usage=Usage(input_tokens=10, output_tokens=5)
    )
    assert response.extract_content() == "Hello, world!"


def test_response_extract_content_blocks():
    """Test Response.extract_content() with content blocks."""
    response = Response(
        content=[TextBlock(text="Hello, "), TextBlock(text="world!")],
        usage=Usage(input_tokens=10, output_tokens=5)
    )
    assert response.extract_content() == "Hello, world!"


def test_tool_call():
    """Test ToolCall model."""
    func_call = FunctionCall(name="calculator", arguments={"a": 1, "b": 2})
    tool_call = ToolCall(id="call_123", function=func_call)
    assert tool_call.id == "call_123"
    assert tool_call.function.name == "calculator"
    assert tool_call.function.arguments == {"a": 1, "b": 2}


def test_chat_options():
    """Test ChatOptions model."""
    options = ChatOptions(
        temperature=0.7,
        max_tokens=100,
        top_p=0.9
    )
    assert options.temperature == 0.7
    assert options.max_tokens == 100
    assert options.top_p == 0.9


def test_chat_options_validation():
    """Test ChatOptions validation."""
    # Temperature should be between 0 and 2
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ChatOptions(temperature=3.0)
    
    # Max tokens should be >= 1
    with pytest.raises(ValidationError):
        ChatOptions(max_tokens=0)
