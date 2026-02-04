"""Mock provider for testing."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from conduit.core.protocols import Capabilities, ChatModel, ModelInfo
from conduit.schema.messages import Message
from conduit.schema.options import ChatOptions
from conduit.schema.responses import Response, Usage


class MockModel(ChatModel):
    """Mock model for testing.

    Examples:
        >>> model = MockModel(response_content="Hello!")
        >>> response = await model.chat([Message(role="user", content="Hi")])
        >>> assert response.extract_content() == "Hello!"
    """

    def __init__(
        self,
        *,
        response_content: str | None = None,
        response: Response | None = None,
        responses: list[Response] | None = None,
        error: Exception | None = None,
        delay: float = 0.0,
        model: str = "mock-model",
    ) -> None:
        """Initialize mock model.

        Args:
            response_content: Content to return in responses (creates simple Response)
            response: Single Response object to return
            responses: List of Response objects to return (cycled through)
            error: Exception to raise (if any)
            delay: Delay in seconds before responding
            model: Model name for model_info()
        """
        if responses is not None:
            self.responses = responses
            self.response_index = 0
        elif response is not None:
            self.responses = [response]
            self.response_index = 0
        elif response_content is not None:
            self.responses = [
                Response(
                    content=response_content,
                    usage=Usage(
                        input_tokens=10,
                        output_tokens=5,
                        total_tokens=15,
                        cache_read_tokens=None,
                        cache_creation_tokens=None,
                    ),
                )
            ]
            self.response_index = 0
        else:
            self.responses = [
                Response(
                    content="Mock response",
                    usage=Usage(
                        input_tokens=10,
                        output_tokens=5,
                        total_tokens=15,
                        cache_read_tokens=None,
                        cache_creation_tokens=None,
                    ),
                )
            ]
            self.response_index = 0

        self.error = error
        self.delay = delay
        self.model = model
        self.call_count = 0
        self.last_messages: list[Message] | None = None
        self.last_options: ChatOptions | None = None

    async def chat(self, messages: list[Message], options: ChatOptions | None = None) -> Response:
        """Return mock response."""
        self.call_count += 1
        self.last_messages = messages
        self.last_options = options

        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.error:
            raise self.error

        # Get response from list (cycle if needed)
        response = self.responses[self.response_index % len(self.responses)]
        self.response_index += 1
        return response

    async def stream(  # type: ignore[override]
        self, messages: list[Message], options: ChatOptions | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream mock response."""
        self.call_count += 1
        self.last_messages = messages
        self.last_options = options

        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.error:
            raise self.error

        # Get response from list (cycle if needed)
        response = self.responses[self.response_index % len(self.responses)]
        self.response_index += 1
        content = response.extract_content()

        for char in content:
            yield {"type": "content_delta", "text": char}

    def model_info(self) -> ModelInfo:
        """Return mock model info."""
        from conduit.core.protocols import ModelInfo

        return ModelInfo(
            provider="mock",
            model=self.model,
            capabilities=Capabilities(
                streaming=True, tool_calling=True, vision=False, json_mode=False, max_context=4096
            ),
        )
