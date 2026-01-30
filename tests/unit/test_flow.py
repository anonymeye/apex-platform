"""Tests for workflow and pipeline composition."""

import pytest

from conduit.flow import Node, Pipeline, WorkflowGraph, compose


@pytest.mark.asyncio
async def test_pipeline_basic():
    """Test basic pipeline execution."""
    pipeline = Pipeline()

    def double(x):
        return x * 2

    def add_one(x):
        return x + 1

    pipeline.add_step(double).add_step(add_one)

    result = await pipeline.run(5)
    assert result == 11  # (5 * 2) + 1


@pytest.mark.asyncio
async def test_pipeline_async():
    """Test pipeline with async steps."""
    pipeline = Pipeline()

    async def async_double(x):
        return x * 2

    def add_one(x):
        return x + 1

    pipeline.add_step(async_double).add_step(add_one)

    result = await pipeline.run(5)
    assert result == 11


@pytest.mark.asyncio
async def test_pipeline_callable():
    """Test pipeline is callable."""
    pipeline = Pipeline()
    pipeline.add_step(lambda x: x * 2)

    result = await pipeline(5)
    assert result == 10


def test_compose():
    """Test compose function."""
    def double(x):
        return x * 2

    def add_one(x):
        return x + 1

    pipeline = compose(double, add_one)
    assert isinstance(pipeline, Pipeline)


@pytest.mark.asyncio
async def test_workflow_graph_basic():
    """Test basic workflow graph execution."""
    graph = WorkflowGraph()

    graph.add_node("step1", lambda x: x * 2)
    graph.add_node("step2", lambda x: x + 1)
    graph.add_edge("step1", "step2")

    results = await graph.run({"step1": 5})

    assert results["step1"] == 10
    assert results["step2"] == 11


@pytest.mark.asyncio
async def test_workflow_graph_multiple_nodes():
    """Test workflow graph with multiple independent nodes."""
    graph = WorkflowGraph()

    graph.add_node("node1", lambda x: x * 2)
    graph.add_node("node2", lambda x: x * 3)

    results = await graph.run({"node1": 5, "node2": 7})

    assert results["node1"] == 10
    assert results["node2"] == 21


@pytest.mark.asyncio
async def test_workflow_graph_chain():
    """Test workflow graph with chain of nodes."""
    graph = WorkflowGraph()

    graph.add_node("a", lambda x: x + 1)
    graph.add_node("b", lambda x: x * 2)
    graph.add_node("c", lambda x: x - 1)

    graph.add_edge("a", "b")
    graph.add_edge("b", "c")

    results = await graph.run({"a": 5})

    assert results["a"] == 6
    assert results["b"] == 12
    assert results["c"] == 11


@pytest.mark.asyncio
async def test_workflow_graph_invalid_edge():
    """Test workflow graph raises error for invalid edges."""
    graph = WorkflowGraph()

    graph.add_node("a", lambda x: x)

    with pytest.raises(ValueError):
        graph.add_edge("a", "nonexistent")

    with pytest.raises(ValueError):
        graph.add_edge("nonexistent", "a")


@pytest.mark.asyncio
async def test_node_execute():
    """Test Node execution."""
    node = Node("test", lambda x: x * 2)
    result = await node.execute(5)
    assert result == 10


@pytest.mark.asyncio
async def test_node_execute_async():
    """Test Node execution with async function."""
    async def async_func(x):
        return x * 2

    node = Node("test", async_func)
    result = await node.execute(5)
    assert result == 10
