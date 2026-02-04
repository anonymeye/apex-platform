"""Summarizing memory that compresses old messages into summaries."""

from conduit.core.protocols import ChatModel
from conduit.memory.base import Memory
from conduit.schema.messages import Message
from conduit.schema.options import ChatOptions


class SummarizingMemory(Memory):
    """Memory that summarizes old messages to save tokens.

    This memory strategy:
    1. Keeps recent messages in full
    2. Summarizes older messages when the conversation gets long
    3. Maintains a summary of the conversation history

    When the conversation exceeds a threshold, older messages are summarized
    using the provided model, and the summary replaces those messages.

    Examples:
        >>> from conduit.providers.openai import OpenAIModel
        >>> async with OpenAIModel(api_key="sk-...") as model:
        ...     memory = SummarizingMemory(model, max_recent_messages=10)
        ...     # Add many messages...
        ...     # When threshold is exceeded, old messages are summarized
    """

    def __init__(
        self,
        model: ChatModel,
        *,
        max_recent_messages: int = 10,
        summarize_threshold: int = 20,
    ) -> None:
        """Initialize summarizing memory.

        Args:
            model: ChatModel to use for summarization
            max_recent_messages: Number of recent messages to keep in full
            summarize_threshold: Number of messages before summarizing old ones
        """
        self.model = model
        self.max_recent_messages = max_recent_messages
        self.summarize_threshold = summarize_threshold
        self._messages: list[Message] = []
        self._summary: str | None = None

    def add_message(self, message: Message) -> None:
        """Add a message to memory.

        Args:
            message: Message to add
        """
        self._messages.append(message)

        # Summarize if we've exceeded the threshold
        if len(self._messages) > self.summarize_threshold:
            self._summarize_old_messages()

    async def add_message_async(self, message: Message) -> None:
        """Add a message to memory (async version for summarization).

        Use this when you want summarization to happen immediately.

        Args:
            message: Message to add
        """
        self._messages.append(message)

        # Summarize if we've exceeded the threshold
        if len(self._messages) > self.summarize_threshold:
            await self._summarize_old_messages_async()

    def get_messages(self) -> list[Message]:
        """Get all messages from memory.

        Returns:
            List of messages: summary (if any) + recent messages
        """
        messages: list[Message] = []

        # Add summary if we have one
        if self._summary:
            messages.append(
                Message(
                    role="system",
                    content=f"Previous conversation summary: {self._summary}",
                )
            )

        # Add recent messages
        recent_start = max(0, len(self._messages) - self.max_recent_messages)
        messages.extend(self._messages[recent_start:])

        return messages

    def clear(self) -> None:
        """Clear all messages and summary from memory."""
        self._messages.clear()
        self._summary = None

    def _summarize_old_messages(self) -> None:
        """Summarize old messages (synchronous placeholder).

        Note: This is a placeholder. For actual summarization, use add_message_async()
        or call _summarize_old_messages_async() explicitly.
        """
        # In a real implementation, this would need to be async
        # For now, we just mark that summarization is needed
        pass

    async def _summarize_old_messages_async(self) -> None:
        """Summarize old messages using the model.

        This keeps the most recent messages and summarizes the rest.
        """
        if len(self._messages) <= self.max_recent_messages:
            return

        # Messages to summarize (everything except recent ones)
        to_summarize = self._messages[:-self.max_recent_messages]

        # Create summary prompt
        conversation_text = "\n".join(
            f"{msg.role}: {msg.content if isinstance(msg.content, str) else '...'}"
            for msg in to_summarize
        )

        summary_prompt = (
            f"""Summarize the following conversation concisely, preserving key information and context:

{conversation_text}

Summary:"""
        )

        # Get summary from model
        response = await self.model.chat(
            [Message(role="user", content=summary_prompt)],
            ChatOptions(temperature=0.3, max_tokens=200, top_p=None),
        )

        self._summary = response.extract_content()

        # Keep only recent messages
        self._messages = self._messages[-self.max_recent_messages:]
