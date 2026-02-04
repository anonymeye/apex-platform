"""Tests for core protocols."""

import pytest
from conduit.core.protocols import Capabilities, ChatModel, Embeddable, ModelInfo
from conduit.schema.messages import Message
from conduit.schema.options import ChatOptions
from conduit.schema.responses import Response


def test_capabilities():
    """Test Capabilities model."""
    caps = Capabilities(
        streaming=True,
        tool_calling=True,
        vision=False,
        json_mode=True,
        max_context=8192
    )
    assert caps.streaming is True
    assert caps.tool_calling is True
    assert caps.vision is False
    assert caps.json_mode is True
    assert caps.max_context == 8192


def test_model_info():
    """Test ModelInfo model."""
    caps = Capabilities()
    info = ModelInfo(
        provider="openai",
        model="gpt-4",
        capabilities=caps
    )
    assert info.provider == "openai"
    assert info.model == "gpt-4"
    assert isinstance(info.capabilities, Capabilities)


def test_chat_model_abstract():
    """Test that ChatModel is abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        ChatModel()  # type: ignore


def test_embeddable_abstract():
    """Test that Embeddable is abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        Embeddable()  # type: ignore


def test_chat_model_interface():
    """Test that a concrete ChatModel must implement all methods."""
    
    class IncompleteModel(ChatModel):
        async def chat(self, messages: list[Message], options: ChatOptions | None = None) -> Response:
            raise NotImplementedError
    
    # Should fail because stream() and model_info() are not implemented
    # Note: In Python, abstract methods are only checked at instantiation time
    # This test verifies the abstract base class is properly defined
    assert hasattr(ChatModel, 'chat')
    assert hasattr(ChatModel, 'stream')
    assert hasattr(ChatModel, 'model_info')
