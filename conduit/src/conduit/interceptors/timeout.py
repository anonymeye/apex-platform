"""Timeout interceptor for request timeouts."""

from dataclasses import dataclass

from conduit.interceptors.context import Context


@dataclass
class TimeoutInterceptor:
    """Enforce timeout on chat requests.

    This interceptor sets metadata that the execution engine uses to wrap
    the model call with asyncio.wait_for. If the request takes longer than
    the specified timeout, it raises a TimeoutError.

    **Important**: This interceptor only works when used with
    `execute_interceptors()`. Direct calls to `model.chat()` will not
    have timeout enforcement.

    The timeout is enforced by the execution engine reading the
    `timeout_seconds` metadata and wrapping the model call with
    `asyncio.wait_for()`.

    Attributes:
        timeout_seconds: Maximum time in seconds for the request

    Examples:
        >>> from conduit.interceptors import execute_interceptors
        >>> from conduit.interceptors.timeout import TimeoutInterceptor
        >>>
        >>> interceptor = TimeoutInterceptor(timeout_seconds=30.0)
        >>> response = await execute_interceptors(
        ...     model, messages, [interceptor]
        ... )
    """

    timeout_seconds: float = 30.0

    async def enter(self, ctx: Context) -> Context:
        """Set up timeout by storing timeout in metadata."""
        ctx.metadata["timeout_seconds"] = self.timeout_seconds
        return ctx
