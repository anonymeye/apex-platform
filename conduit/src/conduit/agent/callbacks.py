"""Callback types and utilities for agent execution."""

from collections.abc import Callable
from typing import Protocol

from conduit.schema.responses import Response, ToolCall


class ToolCallCallback(Protocol):
    """Protocol for tool call callbacks."""

    def __call__(self, tool_call: ToolCall) -> None:
        """Called when a tool is invoked.

        Args:
            tool_call: The tool call being executed
        """
        ...


class ResponseCallback(Protocol):
    """Protocol for response callbacks."""

    def __call__(self, response: Response, iteration: int) -> None:
        """Called when a model response is received.

        Args:
            response: The model response
            iteration: Current iteration number (1-indexed)
        """
        ...


def create_tool_call_logger() -> Callable[[ToolCall], None]:
    """Create a simple tool call logger callback.

    Returns:
        Callback function that logs tool calls

    Examples:
        >>> logger = create_tool_call_logger()
        >>> result = await tool_loop(
        ...     model, messages, tools=[tool],
        ...     on_tool_call=logger
        ... )
    """

    def log_tool_call(tool_call: ToolCall) -> None:
        print(f"[Tool Call] {tool_call.function.name}({tool_call.function.arguments})")

    return log_tool_call


def create_response_logger() -> Callable[[Response, int], None]:
    """Create a simple response logger callback.

    Returns:
        Callback function that logs responses

    Examples:
        >>> logger = create_response_logger()
        >>> result = await tool_loop(
        ...     model, messages, tools=[tool],
        ...     on_response=logger
        ... )
    """

    def log_response(response: Response, iteration: int) -> None:
        content = response.extract_content() if response.content else ""
        has_tools = bool(response.tool_calls)
        print(f"[Response {iteration}] {content[:50]}... (tools: {has_tools})")

    return log_response
