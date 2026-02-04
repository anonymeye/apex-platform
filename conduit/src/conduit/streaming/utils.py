"""Streaming utilities for collecting and processing stream events."""

from collections.abc import AsyncIterator
from typing import Any

from conduit.schema.messages import ContentBlock
from conduit.schema.responses import Response, Usage


async def collect_stream(
    stream: AsyncIterator[dict[str, Any]],
) -> Response:
    """Collect a stream into a complete Response.

    This function consumes an async iterator of stream events and assembles
    them into a complete Response object.

    Args:
        stream: Async iterator of stream events

    Returns:
        Complete Response object

    Examples:
        >>> async with OpenAIModel(api_key="sk-...") as model:
        ...     stream = model.stream([Message(role="user", content="Hello")])
        ...     response = await collect_stream(stream)
        ...     print(response.extract_content())
    """
    content_parts: list[str] = []
    tool_calls: list[dict[str, Any]] | None = None
    model: str | None = None
    stop_reason: str | None = None
    id: str | None = None

    input_tokens = 0
    output_tokens = 0
    total_tokens: int | None = None
    cache_read_tokens: int | None = None
    cache_creation_tokens: int | None = None

    async for event in stream:
        event_type = event.get("type")

        if event_type == "content_delta":
            text = event.get("text", "")
            content_parts.append(text)
        elif event_type == "content_start":
            # Initialize content
            pass
        elif event_type == "content_stop":
            # Content complete
            pass
        elif event_type == "tool_call_start":
            # Initialize tool calls list
            if tool_calls is None:
                tool_calls = []
        elif event_type == "tool_call_delta":
            # Accumulate tool call data
            if tool_calls is not None:
                # This is a simplified version - actual implementation
                # would need to handle tool call accumulation properly
                pass
        elif event_type == "tool_call_stop":
            # Tool call complete
            pass
        elif event_type == "model":
            model = event.get("model")
        elif event_type == "stop_reason":
            stop_reason = event.get("reason")
        elif event_type == "usage":
            usage = event.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = usage.get("total_tokens")
            cache_read_tokens = usage.get("cache_read_tokens")
            cache_creation_tokens = usage.get("cache_creation_tokens")
        elif event_type == "id":
            id = event.get("id")

    # Build content
    content_str = "".join(content_parts)
    content: str | list[ContentBlock] = content_str if content_str else ""

    # Build usage
    usage = Usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_creation_tokens=cache_creation_tokens,
    )

    # Build response
    return Response(
        id=id,
        content=content,
        model=model,
        stop_reason=stop_reason,  # type: ignore[arg-type]
        usage=usage,
        tool_calls=None,  # Tool calls would need more complex accumulation
    )


async def stream_to_string(stream: AsyncIterator[dict[str, Any]]) -> str:
    """Collect stream content into a single string.

    Args:
        stream: Async iterator of stream events

    Returns:
        Complete content string

    Examples:
        >>> async with OpenAIModel(api_key="sk-...") as model:
        ...     stream = model.stream([Message(role="user", content="Hello")])
        ...     content = await stream_to_string(stream)
        ...     print(content)
    """
    content_parts: list[str] = []

    async for event in stream:
        if event.get("type") == "content_delta":
            text = event.get("text", "")
            content_parts.append(text)

    return "".join(content_parts)


async def stream_with_callback(
    stream: AsyncIterator[dict[str, Any]],
    callback: Any,  # Callable[[dict[str, Any]], None]
) -> Response:
    """Collect stream while calling callback for each event.

    Args:
        stream: Async iterator of stream events
        callback: Function to call for each event

    Returns:
        Complete Response object

    Examples:
        >>> def on_event(event):
        ...     if event.get("type") == "content_delta":
        ...         print(event.get("text"), end="", flush=True)
        >>>
        >>> async with OpenAIModel(api_key="sk-...") as model:
        ...     stream = model.stream([Message(role="user", content="Hello")])
        ...     response = await stream_with_callback(stream, on_event)
    """
    content_parts: list[str] = []
    model: str | None = None
    stop_reason: str | None = None
    id: str | None = None

    input_tokens = 0
    output_tokens = 0
    total_tokens: int | None = None
    cache_read_tokens: int | None = None
    cache_creation_tokens: int | None = None

    async for event in stream:
        # Call callback
        callback(event)

        # Process event
        event_type = event.get("type")

        if event_type == "content_delta":
            text = event.get("text", "")
            content_parts.append(text)
        elif event_type == "model":
            model = event.get("model")
        elif event_type == "stop_reason":
            stop_reason = event.get("reason")
        elif event_type == "usage":
            usage = event.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = usage.get("total_tokens")
            cache_read_tokens = usage.get("cache_read_tokens")
            cache_creation_tokens = usage.get("cache_creation_tokens")
        elif event_type == "id":
            id = event.get("id")

    # Build content
    content_str = "".join(content_parts)
    content: str | list[ContentBlock] = content_str if content_str else ""

    # Build usage
    usage = Usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_creation_tokens=cache_creation_tokens,
    )

    # Build response
    return Response(
        id=id,
        content=content,
        model=model,
        stop_reason=stop_reason,  # type: ignore[arg-type]
        usage=usage,
        tool_calls=None,
    )
