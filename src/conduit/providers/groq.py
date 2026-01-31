"""Groq provider implementation."""

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from conduit.core.protocols import Capabilities, ChatModel, ModelInfo
from conduit.errors import (
    AuthenticationError,
    ProviderError,
    RateLimitError,
)
from conduit.schema.messages import Message, TextBlock
from conduit.schema.options import ChatOptions
from conduit.schema.responses import FunctionCall, Response, ToolCall, Usage


class GroqModel(ChatModel):
    """Groq model implementation.

    Examples:
        Basic usage (recommended):
        >>> model = GroqModel(api_key="gsk_...", model="llama-3.3-70b-versatile")
        >>> response = await model.chat([Message(role="user", content="Hello")])
        >>> print(response.extract_content())
        
        Explicit cleanup (optional, for long-running services):
        >>> async with GroqModel(api_key="gsk_...", model="llama-3.3-70b-versatile") as model:
        ...     response = await model.chat([Message(role="user", content="Hello")])
        ...     print(response.extract_content())
        
        Or use close() method:
        >>> model = GroqModel(api_key="gsk_...", model="llama-3.3-70b-versatile")
        >>> response = await model.chat([Message(role="user", content="Hello")])
        >>> await model.close()
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        base_url: str = "https://api.groq.com/openai/v1",
        timeout: float = 60.0,
    ) -> None:
        """Initialize Groq model.

        Args:
            api_key: Groq API key
            model: Model identifier (e.g., "llama-3.3-70b-versatile", "mixtral-8x7b-32768")
            base_url: API base URL (for custom endpoints)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "GroqModel":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client and release resources.
        
        This method is optional - resources will be cleaned up by garbage collection
        if not called explicitly. Use this for explicit cleanup in long-running services.
        """
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def chat(self, messages: list[Message], options: ChatOptions | None = None) -> Response:
        """Send chat request to Groq.

        Args:
            messages: List of messages
            options: Optional chat options

        Returns:
            Response from the model

        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            ProviderError: For other API errors
        """
        opts = options or ChatOptions()  # type: ignore[call-arg]

        # Build request payload (Groq uses OpenAI-compatible format)
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [self._transform_message(msg) for msg in messages],
        }

        # Add optional parameters
        if opts.temperature is not None:
            payload["temperature"] = opts.temperature
        if opts.max_tokens is not None:
            payload["max_tokens"] = opts.max_tokens
        if opts.top_p is not None:
            payload["top_p"] = opts.top_p
        if opts.stop is not None:
            payload["stop"] = opts.stop
        if opts.tools is not None:
            payload["tools"] = opts.tools
        if opts.tool_choice is not None:
            payload["tool_choice"] = opts.tool_choice
        if opts.response_format is not None:
            payload["response_format"] = opts.response_format

        # Make request
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.RequestError as e:
            raise ProviderError(f"Request failed: {str(e)}", provider="groq") from e

        # Parse response
        data = response.json()
        return self._parse_response(data)

    async def stream(  # type: ignore[override]
        self, messages: list[Message], options: ChatOptions | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream chat response from Groq.

        Args:
            messages: List of messages
            options: Optional chat options

        Yields:
            Dictionary with stream events (type, content, etc.)
        """
        opts = options or ChatOptions()  # type: ignore[call-arg]

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [self._transform_message(msg) for msg in messages],
            "stream": True,
        }

        if opts.temperature is not None:
            payload["temperature"] = opts.temperature
        if opts.max_tokens is not None:
            payload["max_tokens"] = opts.max_tokens
        if opts.top_p is not None:
            payload["top_p"] = opts.top_p
        if opts.stop is not None:
            payload["stop"] = opts.stop
        if opts.tools is not None:
            payload["tools"] = opts.tools
        if opts.tool_choice is not None:
            payload["tool_choice"] = opts.tool_choice

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            ) as response:
                response.raise_for_status()

                line_iter = response.aiter_lines()
                try:
                    async for line in line_iter:
                        if not line.strip():
                            continue
                        if line.startswith("data: "):
                            data = line[6:].strip()
                            if data == "[DONE]":
                                break

                            try:
                                event_data = json.loads(data)
                                event = self._parse_stream_event(event_data)
                                if event:
                                    yield event
                            except json.JSONDecodeError:
                                continue
                finally:
                    await line_iter.aclose()
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.RequestError as e:
            raise ProviderError(f"Stream request failed: {str(e)}", provider="groq") from e

    def model_info(self) -> ModelInfo:
        """Get model information."""
        return ModelInfo(
            provider="groq",
            model=self.model,
            capabilities=Capabilities(
                streaming=True,
                tool_calling=True,  # Most Groq models support tool calling
                vision=False,  # Groq models typically don't support vision
                json_mode=True,  # Groq supports JSON mode
                max_context=self._get_context_window(),
            ),
        )

    def _transform_message(self, msg: Message) -> dict[str, Any]:
        """Transform Conduit message to Groq format (OpenAI-compatible)."""
        result: dict[str, Any] = {"role": msg.role}

        # Handle content
        if isinstance(msg.content, str):
            result["content"] = msg.content
        elif isinstance(msg.content, list):
            # Transform content blocks
            content_parts: list[dict[str, Any]] = []
            for block in msg.content:
                if isinstance(block, str):
                    content_parts.append({"type": "text", "text": block})
                elif isinstance(block, TextBlock):
                    content_parts.append({"type": "text", "text": block.text})
                else:
                    # Image block or other - Groq format (OpenAI-compatible)
                    if (
                        hasattr(block, "source")
                        and hasattr(block.source, "url")
                        and block.source.url
                    ):
                        content_parts.append(
                            {"type": block.type, "image_url": {"url": str(block.source.url)}}
                        )
            result["content"] = content_parts
        else:
            result["content"] = str(msg.content)

        if msg.name:
            result["name"] = msg.name
        if msg.tool_call_id:
            result["tool_call_id"] = msg.tool_call_id
        if getattr(msg, "tool_calls", None):
            result["tool_calls"] = [
                {
                    "id": tc["id"] if isinstance(tc, dict) else tc.id,
                    "type": "function",
                    "function": {
                        "name": tc["function"]["name"] if isinstance(tc, dict) else tc.function.name,
                        "arguments": json.dumps(tc["function"]["arguments"])
                        if isinstance(tc, dict)
                        else (
                            json.dumps(tc.function.arguments)
                            if isinstance(tc.function.arguments, dict)
                            else tc.function.arguments
                        ),
                    },
                }
                for tc in msg.tool_calls
            ]

        return result

    def _parse_response(self, data: dict[str, Any]) -> Response:
        """Parse Groq response to Conduit format (OpenAI-compatible)."""
        choice = data["choices"][0]
        message = choice["message"]

        # Extract content
        content = message.get("content", "") or ""

        # Parse usage
        usage_data = data.get("usage", {})
        usage = Usage(
            input_tokens=usage_data.get("prompt_tokens", 0),
            output_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens"),
            cache_read_tokens=None,
            cache_creation_tokens=None,
        )

        # Parse tool calls
        tool_calls = None
        if message.get("tool_calls"):
            tool_calls = [
                ToolCall(
                    id=tc["id"],
                    function=FunctionCall(
                        name=tc["function"]["name"],
                        arguments=(
                            json.loads(tc["function"]["arguments"])
                            if isinstance(tc["function"]["arguments"], str)
                            else tc["function"]["arguments"]
                        ),
                    ),
                )
                for tc in message["tool_calls"]
            ]

        # Parse stop reason
        finish_reason = choice.get("finish_reason")
        stop_reason: str | None = None
        if finish_reason:
            stop_reason = self._parse_stop_reason(finish_reason)

        return Response(
            id=data.get("id"),
            content=content,
            model=data.get("model"),
            stop_reason=stop_reason,  # type: ignore[arg-type]
            usage=usage,
            tool_calls=tool_calls,
        )

    def _parse_stream_event(self, event_data: dict[str, Any]) -> dict[str, Any] | None:
        """Parse SSE event to stream event dict."""
        if "choices" not in event_data or not event_data["choices"]:
            return None

        choice = event_data["choices"][0]
        delta = choice.get("delta", {})

        event: dict[str, Any] = {"type": "content_delta"}

        if "content" in delta:
            event["text"] = delta["content"]

        if "tool_calls" in delta:
            event["type"] = "tool_call_delta"
            event["tool_calls"] = delta["tool_calls"]

        if choice.get("finish_reason"):
            event["type"] = "done"
            event["stop_reason"] = self._parse_stop_reason(choice["finish_reason"])

        return event

    def _parse_stop_reason(self, finish_reason: str) -> str:
        """Parse Groq finish_reason to Conduit stop_reason."""
        from typing import Literal

        mapping: dict[
            str, Literal["end_turn", "tool_use", "max_tokens", "stop_sequence", "content_filter"]
        ] = {
            "stop": "end_turn",
            "tool_calls": "tool_use",
            "length": "max_tokens",
            "content_filter": "content_filter",
        }
        return mapping.get(finish_reason, "end_turn")

    def _handle_http_error(self, error: httpx.HTTPStatusError) -> None:
        """Handle HTTP errors and raise appropriate Conduit errors."""
        status_code = error.response.status_code

        if status_code == 401:
            raise AuthenticationError("Invalid API key", provider="groq", status_code=status_code)
        elif status_code == 429:
            # Try to extract retry_after from headers
            retry_after = None
            if "retry-after" in error.response.headers:
                try:
                    retry_after = float(error.response.headers["retry-after"])
                except ValueError:
                    pass

            raise RateLimitError("Rate limit exceeded", retry_after=retry_after, provider="groq")
        else:
            error_msg = f"API error: {status_code}"
            try:
                error_data = error.response.json()
                if "error" in error_data:
                    error_msg = error_data["error"].get("message", error_msg)
            except Exception:
                pass

            raise ProviderError(error_msg, provider="groq", status_code=status_code)

    def _get_context_window(self) -> int:
        """Get context window size for the model."""
        # Common Groq model context windows
        context_windows = {
            "llama-3.3-70b": 131072,
            "llama-3.1-70b": 131072,
            "llama-3.1-8b": 131072,
            "mixtral-8x7b": 32768,
            "gemma-7b": 8192,
        }

        for model_name, window in context_windows.items():
            if model_name in self.model:
                return window

        # Default
        return 8192
