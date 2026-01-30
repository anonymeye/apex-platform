"""Token-aware windowed memory that maintains a sliding window of messages."""

from conduit.memory.base import Memory
from conduit.schema.messages import Message


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.

    Simple estimation: ~4 characters per token for English text.
    This is a rough approximation - actual tokenization varies by model.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    # Rough estimate: 4 characters per token
    # This is conservative for most models
    return len(text) // 4


def estimate_message_tokens(message: Message) -> int:
    """Estimate token count for a message.

    Args:
        message: Message to estimate tokens for

    Returns:
        Estimated token count
    """
    if isinstance(message.content, str):
        content = message.content
    else:
        # Extract text from content blocks
        content = ""
        for block in message.content:
            if isinstance(block, str):
                content += block
            elif hasattr(block, "text"):
                content += getattr(block, "text", "")

    # Add overhead for role and structure (rough estimate)
    return estimate_tokens(content) + 5


class WindowedMemory(Memory):
    """Token-aware windowed memory that maintains a sliding window.

    This memory strategy keeps only the most recent messages that fit within
    a token budget. When adding a new message would exceed the budget, older
    messages are removed to make room.

    The window always preserves:
    - System messages (if any)
    - The most recent messages that fit within the token limit

    Examples:
        >>> memory = WindowedMemory(max_tokens=100)
        >>> memory.add_message(Message(role="system", content="You are helpful"))
        >>> memory.add_message(Message(role="user", content="Hello"))
        >>> # When adding more messages, older non-system messages are removed
    """

    def __init__(self, max_tokens: int = 4096) -> None:
        """Initialize windowed memory.

        Args:
            max_tokens: Maximum token budget for the window
        """
        self.max_tokens = max_tokens
        self._messages: list[Message] = []
        self._system_messages: list[Message] = []

    def add_message(self, message: Message) -> None:
        """Add a message to memory, maintaining token budget.

        Args:
            message: Message to add
        """
        # Separate system messages
        if message.role == "system":
            self._system_messages.append(message)
            return

        # Add message
        self._messages.append(message)

        # Trim messages to fit within token budget
        self._trim_messages()

    def get_messages(self) -> list[Message]:
        """Get all messages from memory (system + conversation).

        Returns:
            List of messages: system messages first, then conversation messages
        """
        return self._system_messages + self._messages

    def clear(self) -> None:
        """Clear all messages from memory."""
        self._messages.clear()
        self._system_messages.clear()

    def _trim_messages(self) -> None:
        """Trim messages to fit within token budget."""
        # Calculate current token usage
        current_tokens = sum(estimate_message_tokens(msg) for msg in self._messages)
        system_tokens = sum(estimate_message_tokens(msg) for msg in self._system_messages)
        available_tokens = self.max_tokens - system_tokens

        # If we're over budget, remove oldest non-system messages
        while current_tokens > available_tokens and len(self._messages) > 0:
            removed = self._messages.pop(0)
            current_tokens -= estimate_message_tokens(removed)
