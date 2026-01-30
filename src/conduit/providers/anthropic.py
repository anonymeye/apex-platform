"""Anthropic provider implementation."""

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


class AnthropicModel(ChatModel):
    """Anthropic Claude model implementation.

    Examples:
        Basic usage (recommended):
        >>> model = AnthropicModel(api_key="sk-ant-...", model="claude-3-5-sonnet-20241022")
        >>> response = await model.chat([Message(role="user", content="Hello")])
        >>> print(response.extract_content())
        
        Explicit cleanup (optional, for long-running services):
        >>> async with AnthropicModel(
        ...     api_key="sk-ant-...", model="claude-3-5-sonnet-20241022"
        ... ) as model:
        ...     response = await model.chat([Message(role="user", content="Hello")])
        ...     print(response.extract_content())
        
        Or use close() method:
        >>> model = AnthropicModel(api_key="sk-ant-...", model="claude-3-5-sonnet-20241022")
        >>> response = await model.chat([Message(role="user", content="Hello")])
        >>> await model.close()
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        base_url: str = "https://api.anthropic.com/v1",
        timeout: float = 60.0,
    ) -> None:
        """Initialize Anthropic model.

        Args:
            api_key: Anthropic API key
            model: Model identifier (e.g., "claude-3-5-sonnet-20241022", "claude-3-opus-20240229")
            base_url: API base URL (for custom endpoints)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AnthropicModel":
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
        """Send chat request to Anthropic.

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

        # Build request payload
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [self._transform_message(msg) for msg in messages],
        }

        # Anthropic requires max_tokens
        if opts.max_tokens is not None:
            payload["max_tokens"] = opts.max_tokens
        else:
            payload["max_tokens"] = 1024  # Default

        # Add optional parameters
        if opts.temperature is not None:
            payload["temperature"] = opts.temperature
        if opts.top_p is not None:
            payload["top_p"] = opts.top_p
        if opts.stop is not None:
            payload["stop_sequences"] = opts.stop
        if opts.tools is not None:
            payload["tools"] = opts.tools
        if opts.tool_choice is not None:
            # Anthropic uses different format: "auto", "any", or {"type": "tool", "name": "..."}
            if isinstance(opts.tool_choice, str):
                payload["tool_choice"] = opts.tool_choice
            else:
                payload["tool_choice"] = opts.tool_choice

        # Make request
        try:
            response = await self.client.post(
                f"{self.base_url}/messages",
                json=payload,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.RequestError as e:
            raise ProviderError(f"Request failed: {str(e)}", provider="anthropic") from e

        # Parse response
        data = response.json()
        return self._parse_response(data)

    async def stream(  # type: ignore[override]
        self, messages: list[Message], options: ChatOptions | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream chat response from Anthropic.

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

        # Anthropic requires max_tokens
        if opts.max_tokens is not None:
            payload["max_tokens"] = opts.max_tokens
        else:
            payload["max_tokens"] = 1024  # Default

        if opts.temperature is not None:
            payload["temperature"] = opts.temperature
        if opts.top_p is not None:
            payload["top_p"] = opts.top_p
        if opts.stop is not None:
            payload["stop_sequences"] = opts.stop
        if opts.tools is not None:
            payload["tools"] = opts.tools
        if opts.tool_choice is not None:
            if isinstance(opts.tool_choice, str):
                payload["tool_choice"] = opts.tool_choice
            else:
                payload["tool_choice"] = opts.tool_choice

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/messages",
                json=payload,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
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
            raise ProviderError(f"Stream request failed: {str(e)}", provider="anthropic") from e

    def model_info(self) -> ModelInfo:
        """Get model information."""
        return ModelInfo(
            provider="anthropic",
            model=self.model,
            capabilities=Capabilities(
                streaming=True,
                tool_calling=True,
                vision="claude-3" in self.model or "claude-3-5" in self.model,
                json_mode=False,  # Anthropic doesn't have explicit JSON mode
                max_context=self._get_context_window(),
            ),
        )

    def _transform_message(self, msg: Message) -> dict[str, Any]:
        """Transform Conduit message to Anthropic format."""
        result: dict[str, Any] = {"role": msg.role}

        # Anthropic uses content as array of blocks
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
                    # Image block or tool_result/tool_use - handle appropriately
                    if (
                        hasattr(block, "source")
                        and hasattr(block.source, "url")
                        and block.source.url
                    ):
                        content_parts.append(
                            {
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": str(block.source.url),
                                },
                            }
                        )
                    # For tool_result blocks, they should already be in Anthropic format
                    elif hasattr(block, "type") and block.type in ("tool_result", "tool_use"):
                        # Pass through tool blocks as-is - convert to dict
                        if hasattr(block, "model_dump"):
                            content_parts.append(block.model_dump())
                        elif isinstance(block, dict):
                            content_parts.append(block)
                        else:
                            # Fallback: convert to dict representation
                            content_parts.append({"type": getattr(block, "type", "text")})
            result["content"] = content_parts
        else:
            result["content"] = str(msg.content)

        return result

    def _parse_response(self, data: dict[str, Any]) -> Response:
        """Parse Anthropic response to Conduit format."""
        # Anthropic response structure
        content_blocks = data.get("content", [])

        # Extract text content
        text_parts: list[str] = []
        tool_calls = None
        tool_calls_list: list[ToolCall] = []

        for block in content_blocks:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                # Anthropic tool_use format
                tool_calls_list.append(
                    ToolCall(
                        id=block.get("id", ""),
                        function=FunctionCall(
                            name=block.get("name", ""),
                            arguments=block.get("input", {}),
                        ),
                    )
                )

        content = "".join(text_parts) if text_parts else ""

        # Parse usage
        usage_data = data.get("usage", {})
        usage = Usage(
            input_tokens=usage_data.get("input_tokens", 0),
            output_tokens=usage_data.get("output_tokens", 0),
            total_tokens=None,  # Anthropic doesn't provide total
            cache_read_tokens=None,
            cache_creation_tokens=None,
        )

        if tool_calls_list:
            tool_calls = tool_calls_list

        # Parse stop reason
        stop_reason = self._parse_stop_reason(data.get("stop_reason"))

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
        event_type = event_data.get("type")

        if event_type == "content_block_delta":
            delta = event_data.get("delta", {})
            if delta.get("type") == "text_delta":
                return {
                    "type": "content_delta",
                    "text": delta.get("text", ""),
                }
        elif event_type == "content_block_start":
            # Tool use start
            if event_data.get("content_block", {}).get("type") == "tool_use":
                return {
                    "type": "tool_call_delta",
                    "tool_calls": [event_data.get("content_block", {})],
                }
        elif event_type == "message_delta":
            # Final delta with stop reason
            delta = event_data.get("delta", {})
            if delta.get("stop_reason"):
                return {
                    "type": "done",
                    "stop_reason": self._parse_stop_reason(delta.get("stop_reason")),
                }
        elif event_type == "message_stop":
            return {"type": "done"}

        return None

    def _parse_stop_reason(self, stop_reason: str | None) -> str | None:
        """Parse Anthropic stop_reason to Conduit stop_reason."""
        if not stop_reason:
            return None

        from typing import Literal

        mapping: dict[
            str, Literal["end_turn", "tool_use", "max_tokens", "stop_sequence", "content_filter"]
        ] = {
            "end_turn": "end_turn",
            "tool_use": "tool_use",
            "max_tokens": "max_tokens",
            "stop_sequence": "stop_sequence",
        }
        return mapping.get(stop_reason, "end_turn")

    def _handle_http_error(self, error: httpx.HTTPStatusError) -> None:
        """Handle HTTP errors and raise appropriate Conduit errors."""
        status_code = error.response.status_code

        if status_code == 401:
            raise AuthenticationError(
                "Invalid API key", provider="anthropic", status_code=status_code
            )
        elif status_code == 429:
            # Try to extract retry_after from headers
            retry_after = None
            if "retry-after-ms" in error.response.headers:
                try:
                    retry_after = float(error.response.headers["retry-after-ms"]) / 1000.0
                except ValueError:
                    pass
            elif "retry-after" in error.response.headers:
                try:
                    retry_after = float(error.response.headers["retry-after"])
                except ValueError:
                    pass

            raise RateLimitError(
                "Rate limit exceeded", retry_after=retry_after, provider="anthropic"
            )
        else:
            error_msg = f"API error: {status_code}"
            try:
                error_data = error.response.json()
                if "error" in error_data:
                    error_msg = error_data["error"].get("message", error_msg)
            except Exception:
                pass

            raise ProviderError(error_msg, provider="anthropic", status_code=status_code)

    def _get_context_window(self) -> int:
        """Get context window size for the model."""
        # Common Anthropic model context windows
        context_windows = {
            "claude-3-5-sonnet": 200000,
            "claude-3-opus": 200000,
            "claude-3-sonnet": 200000,
            "claude-3-haiku": 200000,
            "claude-2": 100000,
        }

        for model_name, window in context_windows.items():
            if model_name in self.model:
                return window

        # Default
        return 200000
