"""Agent tool loop implementation."""

from collections.abc import Callable
from dataclasses import dataclass

from conduit.core.protocols import ChatModel
from conduit.errors import MaxIterationsError
from conduit.interceptors.base import Interceptor
from conduit.interceptors.execution import execute_interceptors
from conduit.schema.messages import Message
from conduit.schema.options import ChatOptions
from conduit.schema.responses import Response, ToolCall
from conduit.tools import Tool, execute_tool_calls


@dataclass
class AgentResult:
    """Result from agent execution.

    Attributes:
        response: Final response from the model
        messages: Complete message history (including tool calls and results)
        iterations: Number of loop iterations executed
        tool_calls_made: List of all tool calls made during execution

    Examples:
        >>> result = await tool_loop(model, messages, tools=[weather_tool])
        >>> print(f"Completed in {result.iterations} iterations")
        >>> print(f"Made {len(result.tool_calls_made)} tool calls")
    """

    response: Response
    messages: list[Message]
    iterations: int
    tool_calls_made: list[ToolCall]


async def tool_loop(
    model: ChatModel,
    messages: list[Message],
    *,
    tools: list[Tool],
    max_iterations: int = 10,
    on_tool_call: Callable[[ToolCall], None] | None = None,
    on_response: Callable[[Response, int], None] | None = None,
    chat_opts: ChatOptions | None = None,
    interceptors: list[Interceptor] | None = None,
) -> AgentResult:
    """Run agent tool loop until completion.

    This function implements an autonomous agent loop that:
    1. Sends messages to the model
    2. Checks if the model wants to call tools
    3. Executes tool calls if requested
    4. Adds tool results back to the conversation
    5. Repeats until the model returns a final response (no tool calls)

    The loop continues until:
    - The model returns a response without tool calls (success)
    - Maximum iterations are reached (raises MaxIterationsError)

    Args:
        model: ChatModel instance
        messages: Initial messages (should include system/user messages)
        tools: Available tools for the agent
        max_iterations: Maximum number of loop iterations (default: 10)
        on_tool_call: Optional callback called for each tool call
        on_response: Optional callback called for each model response
        chat_opts: Optional chat options (will be updated with tools)
        interceptors: Optional list of interceptors to apply to model calls

    Returns:
        AgentResult with final response, message history, and metadata

    Raises:
        MaxIterationsError: If max iterations reached without completion

    Examples:
        >>> from conduit.providers.openai import OpenAIModel
        >>> from conduit.schema.messages import Message
        >>> from conduit.interceptors.retry import RetryInterceptor
        >>>
        >>> async with OpenAIModel(api_key="sk-...") as model:
        ...     result = await tool_loop(
        ...         model=model,
        ...         messages=[Message(role="user", content="What's the weather?")],
        ...         tools=[weather_tool],
        ...         max_iterations=5,
        ...         interceptors=[RetryInterceptor(max_attempts=3)],
        ...         on_tool_call=lambda call: print(f"Calling {call.function.name}"),
        ...         on_response=lambda resp, it: print(f"Iteration {it}")
        ...     )
        ...     print(result.response.extract_content())
    """
    # Prepare chat options with tools
    opts = chat_opts or ChatOptions()  # type: ignore[call-arg]
    # Convert tools to JSON Schema format
    opts.tools = [tool.to_json_schema() for tool in tools]

    current_messages = list(messages)
    all_tool_calls: list[ToolCall] = []
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Call model (with interceptors if provided)
        if interceptors:
            response = await execute_interceptors(
                model, current_messages, interceptors, opts
            )
        else:
            response = await model.chat(current_messages, opts)

        # Callback for response
        if on_response:
            on_response(response, iteration)

        # Check if done (no tool calls means final response)
        if not response.tool_calls:
            # Add final response to message history
            content = (
                response.content
                if isinstance(response.content, str)
                else response.extract_content()
            )
            final_messages = current_messages + [Message(role="assistant", content=content)]
            return AgentResult(
                response=response,
                messages=final_messages,
                iterations=iteration,
                tool_calls_made=all_tool_calls,
            )

        # Execute tools
        for tool_call in response.tool_calls:
            if on_tool_call:
                on_tool_call(tool_call)
            all_tool_calls.append(tool_call)

        # Add assistant message with content (tool calls are in response)
        content = (
            response.content if isinstance(response.content, str) else response.extract_content()
        )
        current_messages.append(Message(role="assistant", content=content))

        # Execute tools and add results
        tool_results = await execute_tool_calls(tools, response.tool_calls)
        for result in tool_results:
            current_messages.append(Message(**result))

    # Max iterations reached
    raise MaxIterationsError(f"Agent exceeded maximum iterations ({max_iterations})")
