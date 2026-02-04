"""Base memory protocol for conversation management."""

from abc import ABC, abstractmethod

from conduit.schema.messages import Message


class Memory(ABC):
    """Abstract base class for memory management strategies.

    Memory classes manage conversation history, providing different strategies
    for maintaining context while staying within token limits.

    Examples:
        >>> from conduit.memory import ConversationMemory
        >>> memory = ConversationMemory()
        >>> memory.add_message(Message(role="user", content="Hello"))
        >>> messages = memory.get_messages()
    """

    @abstractmethod
    def add_message(self, message: Message) -> None:
        """Add a message to memory.

        Args:
            message: Message to add
        """
        ...

    @abstractmethod
    def get_messages(self) -> list[Message]:
        """Get all messages from memory.

        Returns:
            List of messages in conversation order
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all messages from memory."""
        ...

    def __len__(self) -> int:
        """Return number of messages in memory."""
        return len(self.get_messages())
