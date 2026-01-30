"""Base interceptor protocol."""

from typing import Protocol

from conduit.interceptors.context import Context


class Interceptor(Protocol):
    """Protocol for interceptors.

    Interceptors can implement any combination of enter, leave, and error methods.
    Methods that are not implemented will be no-ops.

    Examples:
        >>> class MyInterceptor:
        ...     async def enter(self, ctx: Context) -> Context:
        ...         # Modify context before model call
        ...         return ctx
        ...
        ...     async def leave(self, ctx: Context) -> Context:
        ...         # Process response after model call
        ...         return ctx
        ...
        ...     async def error(self, ctx: Context, error: Exception) -> Context:
        ...         # Handle errors
        ...         return ctx
    """

    async def enter(self, ctx: Context) -> Context:
        """Called before the model call.

        This method is called in forward order through the interceptor chain.
        Interceptors can modify the context, including messages and options.

        Args:
            ctx: Current context

        Returns:
            Modified context
        """
        return ctx

    async def leave(self, ctx: Context) -> Context:
        """Called after successful model call.

        This method is called in reverse order through the interceptor chain.
        Interceptors can process or modify the response.

        Args:
            ctx: Current context with response set

        Returns:
            Modified context
        """
        return ctx

    async def error(self, ctx: Context, error: Exception) -> Context:
        """Called when an error occurs.

        This method is called in reverse order through the interceptor chain
        when an error occurs. Interceptors can handle the error or clear it
        to allow retry.

        Args:
            ctx: Current context
            error: The exception that occurred

        Returns:
            Modified context (can clear error to continue)
        """
        ctx.error = error
        return ctx
