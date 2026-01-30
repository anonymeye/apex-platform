"""Async/sync utilities."""

import asyncio
from collections.abc import Coroutine
from typing import TypeVar

T = TypeVar("T")


def run_sync(coro: Coroutine[None, None, T]) -> T:
    """Run async coroutine synchronously.
    
    This function safely runs an async coroutine in a synchronous context.
    It will raise an error if called from within an already-running event loop
    (e.g., FastAPI, Jupyter, async frameworks).
    
    Args:
        coro: Async coroutine to run
        
    Returns:
        Result of the coroutine
        
    Raises:
        RuntimeError: If called from async context with running event loop
        
    Examples:
        >>> async def async_func():
        ...     return "result"
        >>> result = run_sync(async_func())
        >>> print(result)
        'result'
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No loop running - safe to use asyncio.run()
        return asyncio.run(coro)
    
    # Loop is running - cannot use sync API
    raise RuntimeError(
        "Cannot use synchronous API from async context "
        "(FastAPI, Jupyter, etc.). Use async methods instead:\n"
        "  - Use agent.ainvoke() instead of agent.invoke()\n"
        "  - Use await model.chat() instead of model.chat()"
    )
