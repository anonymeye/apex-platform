"""Tests for async utilities."""

import asyncio
import pytest

from conduit.utils.async_utils import run_sync


async def sample_async_func(value: int) -> int:
    """Sample async function for testing."""
    await asyncio.sleep(0.01)
    return value * 2


def test_run_sync_basic():
    """Test run_sync with basic async function."""
    result = run_sync(sample_async_func(5))
    assert result == 10


def test_run_sync_with_exception():
    """Test run_sync propagates exceptions."""
    async def failing_func():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError, match="Test error"):
        run_sync(failing_func())


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
async def test_run_sync_from_async_context():
    """Test that run_sync raises error when called from async context."""
    with pytest.raises(RuntimeError, match="Cannot use synchronous API from async context"):
        # Intentionally not awaiting - this is what we're testing
        # The coroutine is created but not awaited to trigger the error
        run_sync(sample_async_func(5))


def test_run_sync_multiple_calls():
    """Test multiple sequential run_sync calls."""
    result1 = run_sync(sample_async_func(3))
    result2 = run_sync(sample_async_func(7))
    
    assert result1 == 6
    assert result2 == 14
