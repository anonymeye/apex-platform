"""Core protocols for Conduit."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from conduit.schema.messages import Message
from conduit.schema.options import ChatOptions
from conduit.schema.responses import Response


class Capabilities(BaseModel):
    """Model capabilities."""

    streaming: bool = True
    tool_calling: bool = False
    vision: bool = False
    json_mode: bool = False
    max_context: int = 4096


class ModelInfo(BaseModel):
    """Model information."""

    provider: str
    model: str
    capabilities: Capabilities


class ChatModel(ABC):
    """Abstract base class for chat models."""

    @abstractmethod
    async def chat(self, messages: list[Message], options: ChatOptions | None = None) -> Response:
        """Send messages to the model and receive a response (async).

        Args:
            messages: List of messages in the conversation
            options: Optional chat options (temperature, max_tokens, etc.)

        Returns:
            Response from the model

        Raises:
            ProviderError: If the API call fails
            ValidationError: If the input is invalid
        """
        ...

    @abstractmethod
    async def stream(
        self, messages: list[Message], options: ChatOptions | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream response from the model.

        Args:
            messages: List of messages in the conversation
            options: Optional chat options

        Yields:
            Dictionary with stream events (content_delta, etc.)

        Raises:
            ProviderError: If the API call fails
            ValidationError: If the input is invalid
        """
        ...

    @abstractmethod
    def model_info(self) -> ModelInfo:
        """Get information about this model.

        Returns:
            ModelInfo with provider, model name, and capabilities
        """
        ...


class Embeddable(ABC):
    """Abstract base class for embedding models."""

    @abstractmethod
    async def embed(
        self, texts: str | list[str], options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generate embeddings for text(s).

        Args:
            texts: Single text string or list of text strings
            options: Optional embedding options

        Returns:
            Dictionary with embeddings (typically 'embeddings' key)

        Raises:
            ProviderError: If the API call fails
            ValidationError: If the input is invalid
        """
        ...
