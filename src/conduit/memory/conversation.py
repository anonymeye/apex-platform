"""Simple conversation memory that stores all messages."""

from conduit.memory.base import Memory
from conduit.schema.messages import Message


class ConversationMemory(Memory):
    """Simple memory that stores all messages without any filtering.

    This is the simplest memory strategy - it keeps all messages in order.
    Use this when you don't have token limits or want to preserve full context.

    Examples:
        >>> memory = ConversationMemory()
        >>> memory.add_message(Message(role="user", content="Hello"))
        >>> memory.add_message(Message(role="assistant", content="Hi there!"))
        >>> messages = memory.get_messages()
        >>> assert len(messages) == 2
    """

    def __init__(self) -> None:
        """Initialize conversation memory."""
        self._messages: list[Message] = []

    def add_message(self, message: Message) -> None:
        """Add a message to memory.

        Args:
            message: Message to add
        """
        self._messages.append(message)

    def get_messages(self) -> list[Message]:
        """Get all messages from memory.

        Returns:
            List of all messages in conversation order
        """
        return list(self._messages)

    def clear(self) -> None:
        """Clear all messages from memory."""
        self._messages.clear()
