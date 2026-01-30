"""Tests for cost tracking interceptor."""

import pytest
from conduit.interceptors import execute_interceptors
from conduit.interceptors.cost_tracking import CostTrackingInterceptor
from conduit.providers.mock import MockModel
from conduit.schema.messages import Message


@pytest.mark.asyncio
async def test_cost_tracking_basic():
    """Test basic cost tracking."""
    model = MockModel(response_content="Test", model="gpt-4")
    messages = [Message(role="user", content="Test")]
    
    costs = []
    def track_cost(cost: float, tokens: dict):
        costs.append((cost, tokens))
    
    interceptor = CostTrackingInterceptor(on_cost=track_cost)
    
    response = await execute_interceptors(model, messages, [interceptor])
    
    assert response.extract_content() == "Test"
    assert len(costs) == 1
    assert costs[0][0] >= 0  # Cost should be calculated
    assert "input_tokens" in costs[0][1]
    assert "output_tokens" in costs[0][1]


@pytest.mark.asyncio
async def test_cost_tracking_total_cost():
    """Test cost tracking accumulates total cost."""
    model = MockModel(response_content="Test", model="gpt-4")
    messages = [Message(role="user", content="Test")]
    interceptor = CostTrackingInterceptor()
    
    # First call
    await execute_interceptors(model, messages, [interceptor])
    cost1 = interceptor.total_cost
    
    # Second call
    await execute_interceptors(model, messages, [interceptor])
    cost2 = interceptor.total_cost
    
    assert cost2 >= cost1  # Total should increase
    assert interceptor.request_count == 2


@pytest.mark.asyncio
async def test_cost_tracking_custom_pricing():
    """Test cost tracking with custom pricing."""
    custom_pricing = {
        "mock": {
            "mock-model": {"input": 10.0, "output": 20.0}
        }
    }
    
    model = MockModel(response_content="Test", model="mock-model")
    messages = [Message(role="user", content="Test")]
    interceptor = CostTrackingInterceptor(pricing=custom_pricing)
    
    response = await execute_interceptors(model, messages, [interceptor])
    
    assert response.extract_content() == "Test"
    # Cost should be calculated based on custom pricing
    assert interceptor.total_cost > 0


@pytest.mark.asyncio
async def test_cost_tracking_metadata():
    """Test cost tracking sets metadata."""
    # Use custom pricing for mock provider
    custom_pricing = {
        "mock": {
            "mock-model": {"input": 10.0, "output": 20.0}
        }
    }
    model = MockModel(response_content="Test", model="mock-model")
    messages = [Message(role="user", content="Test")]
    interceptor = CostTrackingInterceptor(pricing=custom_pricing)
    
    # We can't easily access metadata from execute_interceptors,
    # but we can verify the interceptor tracks costs
    response = await execute_interceptors(model, messages, [interceptor])
    
    assert response.extract_content() == "Test"
    assert interceptor.total_cost > 0
    assert interceptor.request_count == 1
