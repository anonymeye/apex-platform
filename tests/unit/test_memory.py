"""Tests for memory management."""

import pytest

from conduit.memory import ConversationMemory, SummarizingMemory, WindowedMemory
from conduit.providers.mock import MockModel
from conduit.schema.messages import Message
from conduit.schema.responses import Response, Usage


def test_conversation_memory():
    """Test ConversationMemory stores all messages."""
    memory = ConversationMemory()

    assert len(memory) == 0
    assert memory.get_messages() == []

    memory.add_message(Message(role="user", content="Hello"))
    assert len(memory) == 1

    memory.add_message(Message(role="assistant", content="Hi there!"))
    assert len(memory) == 2

    messages = memory.get_messages()
    assert len(messages) == 2
    assert messages[0].content == "Hello"
    assert messages[1].content == "Hi there!"

    memory.clear()
    assert len(memory) == 0


def test_windowed_memory():
    """Test WindowedMemory maintains token budget."""
    memory = WindowedMemory(max_tokens=100)

    # Add system message (should be preserved)
    memory.add_message(Message(role="system", content="You are helpful"))
    assert len(memory.get_messages()) == 1

    # Add many messages
    for i in range(20):
        memory.add_message(Message(role="user", content=f"Message {i} " * 10))

    # Should have system message + recent messages that fit
    messages = memory.get_messages()
    assert messages[0].role == "system"
    assert len(messages) <= 20  # Should be trimmed


def test_windowed_memory_preserves_system():
    """Test WindowedMemory always preserves system messages."""
    memory = WindowedMemory(max_tokens=50)

    # Add system message
    memory.add_message(Message(role="system", content="System message"))

    # Add many user messages
    for i in range(10):
        memory.add_message(Message(role="user", content="User message " * 5))

    messages = memory.get_messages()
    # System message should always be first
    assert messages[0].role == "system"
    assert messages[0].content == "System message"


@pytest.mark.asyncio
async def test_summarizing_memory():
    """Test SummarizingMemory basic functionality."""
    model = MockModel(response_content="Summary of conversation")
    memory = SummarizingMemory(model, max_recent_messages=5, summarize_threshold=10)

    # Add messages below threshold
    for i in range(5):
        memory.add_message(Message(role="user", content=f"Message {i}"))

    messages = memory.get_messages()
    assert len(messages) == 5  # No summary yet

    # Add more messages to trigger summarization
    for i in range(5, 10):
        memory.add_message(Message(role="user", content=f"Message {i}"))

    # Should still have messages (summarization is async)
    messages = memory.get_messages()
    assert len(messages) >= 5


@pytest.mark.asyncio
async def test_summarizing_memory_async():
    """Test SummarizingMemory with async summarization."""
    model = MockModel(response_content="This is a summary of the conversation")
    memory = SummarizingMemory(model, max_recent_messages=3, summarize_threshold=5)

    # Add messages below threshold
    for i in range(5):
        await memory.add_message_async(Message(role="user", content=f"Message {i}"))

    # Add one more to trigger summarization (now we have 6 > 5)
    await memory.add_message_async(Message(role="user", content="Message 5"))

    # Should have summary + recent messages
    messages = memory.get_messages()
    # Summary should be added as system message
    assert any(msg.role == "system" and "summary" in msg.content.lower() for msg in messages)


def test_memory_clear():
    """Test that clear() works for all memory types."""
    memories = [
        ConversationMemory(),
        WindowedMemory(max_tokens=100),
    ]

    for memory in memories:
        memory.add_message(Message(role="user", content="Test"))
        assert len(memory) > 0

        memory.clear()
        assert len(memory) == 0
        assert memory.get_messages() == []
