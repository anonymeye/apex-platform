"""Tool execution utilities."""

from typing import TYPE_CHECKING, Any

from conduit.schema.responses import ToolCall

if TYPE_CHECKING:
    from conduit.tools.definition import Tool


async def execute_tool_calls(
    tools: list["Tool"], tool_calls: list[ToolCall]
) -> list[dict[str, Any]]:
    """Execute multiple tool calls and return results as messages.

    This function takes a list of ToolCall objects from the LLM response,
    finds the corresponding Tool definitions, executes them, and returns
    the results in the format expected for tool result messages.

    Args:
        tools: Available tools (list of Tool instances)
        tool_calls: Tool calls from model response

    Returns:
        List of tool result message dicts:
        [
            {
                "role": "tool",
                "tool_call_id": "...",
                "content": "..."  # Result as string
            },
            ...
        ]

    Examples:
        >>> from conduit.schema.responses import ToolCall, FunctionCall
        >>>
        >>> tool_calls = [
        ...     ToolCall(
        ...         id="call_123",
        ...         function=FunctionCall(
        ...             name="get_weather",
        ...             arguments={"location": "Tokyo"}
        ...         )
        ...     )
        ... ]
        >>>
        >>> results = await execute_tool_calls([weather_tool], tool_calls)
        >>> # results = [{"role": "tool", "tool_call_id": "call_123", "content": "..."}]
    """
    results: list[dict[str, Any]] = []

    for call in tool_calls:
        # Find tool by name
        tool = next((t for t in tools if t.name == call.function.name), None)
        if not tool:
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": f"Error: Tool '{call.function.name}' not found",
                }
            )
            continue

        # Execute tool
        try:
            result = tool.execute(call.function.arguments)
            # Convert result to string if needed
            if isinstance(result, str):
                content = result
            elif isinstance(result, dict):
                # Try to convert dict to JSON string
                import json

                content = json.dumps(result)
            else:
                content = str(result)
        except Exception as e:
            content = f"Error executing tool: {str(e)}"

        results.append({"role": "tool", "tool_call_id": call.id, "content": content})

    return results
