"""Graph-based workflow for complex LLM orchestration."""

from collections.abc import Awaitable, Callable
from typing import Any


class Node:
    """A node in a workflow graph.

    Each node represents an operation that can process input and produce output.
    Nodes can be connected to form a directed graph.

    Examples:
        >>> node = Node("process", lambda x: x * 2)
        >>> result = await node.execute(5)
        >>> assert result == 10
    """

    def __init__(
        self,
        name: str,
        func: Callable[[Any], Awaitable[Any] | Any],
        *,
        inputs: list[str] | None = None,
    ) -> None:
        """Initialize a node.

        Args:
            name: Unique name for the node
            func: Function to execute (can be async)
            inputs: Optional list of input node names (for validation)
        """
        self.name = name
        self.func = func
        self.inputs = inputs or []
        self.outputs: list[str] = []

    async def execute(self, input_data: Any) -> Any:
        """Execute the node function.

        Args:
            input_data: Input data

        Returns:
            Output from the function
        """
        result = self.func(input_data)
        if isinstance(result, Awaitable):
            return await result
        return result


class WorkflowGraph:
    """Graph-based workflow for orchestrating multiple LLM operations.

    A workflow graph allows you to define complex operations with multiple
    nodes and edges. Nodes can depend on outputs from other nodes.

    Examples:
        >>> graph = WorkflowGraph()
        >>> graph.add_node("preprocess", preprocess_messages)
        >>> graph.add_node("call_model", lambda msgs: model.chat(msgs))
        >>> graph.add_edge("preprocess", "call_model")
        >>> result = await graph.run({"preprocess": [Message(role="user", content="Hello")]})
    """

    def __init__(self) -> None:
        """Initialize empty workflow graph."""
        self._nodes: dict[str, Node] = {}
        self._edges: dict[str, list[str]] = {}  # node -> list of target nodes

    def add_node(
        self,
        name: str,
        func: Callable[[Any], Awaitable[Any] | Any],
        *,
        inputs: list[str] | None = None,
    ) -> "WorkflowGraph":
        """Add a node to the graph.

        Args:
            name: Unique node name
            func: Function to execute (can be async)
            inputs: Optional list of input node names

        Returns:
            Self for method chaining

        Examples:
            >>> graph = WorkflowGraph()
            >>> graph.add_node("step1", func1).add_node("step2", func2)
        """
        self._nodes[name] = Node(name, func, inputs=inputs)
        if name not in self._edges:
            self._edges[name] = []
        return self

    def add_edge(self, source: str, target: str) -> "WorkflowGraph":
        """Add an edge from source node to target node.

        Args:
            source: Source node name
            target: Target node name

        Returns:
            Self for method chaining

        Raises:
            ValueError: If source or target node doesn't exist

        Examples:
            >>> graph.add_edge("preprocess", "call_model")
        """
        if source not in self._nodes:
            raise ValueError(f"Source node '{source}' does not exist")
        if target not in self._nodes:
            raise ValueError(f"Target node '{target}' does not exist")

        self._edges[source].append(target)
        self._nodes[target].inputs.append(source)
        return self

    async def run(self, initial_data: dict[str, Any]) -> dict[str, Any]:
        """Run the workflow graph.

        Args:
            initial_data: Dictionary mapping node names to initial input data

        Returns:
            Dictionary mapping node names to their outputs

        Examples:
            >>> results = await graph.run({
            ...     "preprocess": [Message(role="user", content="Hello")]
            ... })
            >>> print(results["call_model"])
        """
        # Track outputs for each node
        outputs: dict[str, Any] = {}

        # Initialize with provided data
        outputs.update(initial_data)

        # Topological sort to determine execution order
        execution_order = self._topological_sort()

        # Execute nodes in order
        for node_name in execution_order:
            node = self._nodes[node_name]

            # Determine input data
            if node_name in outputs and not node.inputs:
                # Node already has output from initial_data and has no inputs
                # Use the provided value as input and execute
                input_data = outputs[node_name]
                result = await node.execute(input_data)
                outputs[node_name] = result
            elif node_name in outputs:
                # Node has output from initial_data but also has inputs
                # This means it was provided as input - execute it
                input_data = outputs[node_name]
                result = await node.execute(input_data)
                outputs[node_name] = result
            else:
                # Node doesn't have output yet - collect from inputs
                if node.inputs:
                    # For nodes with multiple inputs, combine them
                    input_data = [outputs[inp] for inp in node.inputs if inp in outputs]
                    if len(input_data) == 1:
                        input_data = input_data[0]
                    elif len(input_data) > 1:
                        # Multiple inputs - pass as tuple
                        input_data = tuple(input_data)
                    else:
                        # No inputs found - use None
                        input_data = None
                else:
                    # Node with no inputs - use None
                    input_data = None

                # Execute node
                result = await node.execute(input_data)
                outputs[node_name] = result

        return outputs

    def _topological_sort(self) -> list[str]:
        """Perform topological sort of nodes.

        Returns:
            List of node names in execution order
        """
        # Simple topological sort using Kahn's algorithm
        in_degree: dict[str, int] = {name: 0 for name in self._nodes}

        # Calculate in-degrees
        for targets in self._edges.values():
            for target in targets:
                in_degree[target] = in_degree.get(target, 0) + 1

        # Find nodes with no incoming edges
        queue: list[str] = [name for name, degree in in_degree.items() if degree == 0]
        result: list[str] = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # Reduce in-degree of neighbors
            for target in self._edges.get(node, []):
                in_degree[target] -= 1
                if in_degree[target] == 0:
                    queue.append(target)

        # Check for cycles
        if len(result) != len(self._nodes):
            raise ValueError("Workflow graph contains cycles")

        return result
