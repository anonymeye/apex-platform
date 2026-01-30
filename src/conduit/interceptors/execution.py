"""Interceptor chain execution."""

import asyncio

from conduit.core.protocols import ChatModel
from conduit.interceptors.base import Interceptor
from conduit.interceptors.context import Context
from conduit.schema.messages import Message
from conduit.schema.options import ChatOptions
from conduit.schema.responses import Response


async def execute_interceptors(
    model: ChatModel,
    messages: list[Message],
    interceptors: list[Interceptor],
    opts: ChatOptions | None = None,
) -> Response:
    """Execute chat with interceptor chain.

    The execution flow is:
    1. Enter phase: Call enter() on each interceptor in forward order
    2. Model call: Call the model's chat() method
    3. Error phase (if error): Call error() on each interceptor in reverse order
    4. Leave phase: Call leave() on each interceptor in reverse order

    Args:
        model: ChatModel instance
        messages: Messages to send
        interceptors: List of interceptors to apply
        opts: Optional chat options

    Returns:
        Response from model

    Raises:
        Exception: If error occurs and is not handled by interceptors

    Examples:
        >>> from conduit.interceptors import execute_interceptors
        >>> from conduit.interceptors.retry import RetryInterceptor
        >>>
        >>> interceptors = [RetryInterceptor(max_attempts=3)]
        >>> response = await execute_interceptors(
        ...     model, messages, interceptors
        ... )
    """
    ctx = Context(
        model=model,
        messages=messages,
        opts=opts if opts is not None else ChatOptions(),  # type: ignore[call-arg]
    )

    # Enter phase (forward through interceptors)
    for interceptor in interceptors:
        if ctx.terminated:
            break
        try:
            if hasattr(interceptor, "enter"):
                ctx = await interceptor.enter(ctx)
        except Exception as e:
            ctx.error = e
            break

    # Model call (if not terminated and no error)
    if not ctx.terminated and not ctx.error:
        try:
            # Check for timeout in metadata
            timeout = ctx.metadata.get("timeout_seconds")
            if timeout is not None:
                ctx.response = await asyncio.wait_for(
                    model.chat(ctx.get_messages(), ctx.get_opts()), timeout=timeout
                )
            else:
                ctx.response = await model.chat(ctx.get_messages(), ctx.get_opts())
        except asyncio.TimeoutError:
            from conduit.errors import TimeoutError

            timeout_val = ctx.metadata.get("timeout_seconds", 0)
            ctx.error = TimeoutError(f"Request timed out after {timeout_val} seconds")
        except Exception as e:
            ctx.error = e

    # Error phase (if error occurred)
    if ctx.error:
        for interceptor in reversed(interceptors):
            try:
                if hasattr(interceptor, "error"):
                    ctx = await interceptor.error(ctx, ctx.error)
                    if not ctx.error:  # Error was cleared
                        break
            except Exception as e:
                ctx.error = e

    # Leave phase (backward through interceptors)
    for interceptor in reversed(interceptors):
        try:
            if hasattr(interceptor, "leave"):
                ctx = await interceptor.leave(ctx)
        except Exception as e:
            ctx.error = e

    # Raise if error remains
    if ctx.error:
        raise ctx.error

    if ctx.response is None:
        raise RuntimeError("No response received from model")

    return ctx.response
