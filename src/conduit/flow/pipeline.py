"""Pipeline composition for chaining LLM operations."""

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

T = TypeVar("T")
U = TypeVar("U")


class Pipeline:
    """Pipeline for chaining LLM operations.

    A pipeline allows you to compose multiple operations that process messages
    or responses in sequence. Each step can transform the data before passing
    it to the next step.

    Examples:
        >>> async def add_system_message(messages):
        ...     return [Message(role="system", content="Be helpful")] + messages
        >>>
        >>> async def extract_text(response):
        ...     return response.extract_content()
        >>>
        >>> pipeline = Pipeline()
        >>> pipeline.add_step(add_system_message)
        >>> pipeline.add_step(lambda msgs: model.chat(msgs))
        >>> pipeline.add_step(extract_text)
        >>> result = await pipeline.run([Message(role="user", content="Hello")])
    """

    def __init__(self) -> None:
        """Initialize empty pipeline."""
        self._steps: list[Callable[[Any], Awaitable[Any] | Any]] = []

    def add_step(self, step: Callable[[Any], Awaitable[Any] | Any]) -> "Pipeline":
        """Add a step to the pipeline.

        Args:
            step: Function that takes input and returns output (can be async)

        Returns:
            Self for method chaining

        Examples:
            >>> pipeline = Pipeline()
            >>> pipeline.add_step(transform_messages).add_step(call_model)
        """
        self._steps.append(step)
        return self

    async def run(self, initial_input: Any) -> Any:
        """Run the pipeline with initial input.

        Args:
            initial_input: Input to the first step

        Returns:
            Output from the last step

        Examples:
            >>> result = await pipeline.run([Message(role="user", content="Hello")])
        """
        current = initial_input

        for step in self._steps:
            if isinstance(step, Awaitable):
                current = await step
            elif callable(step):
                result = step(current)
                if isinstance(result, Awaitable):
                    current = await result
                else:
                    current = result
            else:
                current = step

        return current

    def __call__(self, initial_input: Any) -> Awaitable[Any]:
        """Make pipeline callable.

        Args:
            initial_input: Input to the pipeline

        Returns:
            Awaitable result
        """
        return self.run(initial_input)


def compose(*steps: Callable[[Any], Awaitable[Any] | Any]) -> Pipeline:
    """Compose multiple steps into a pipeline.

    Args:
        *steps: Variable number of step functions

    Returns:
        Pipeline with all steps added

    Examples:
        >>> pipeline = compose(
        ...     add_system_message,
        ...     lambda msgs: model.chat(msgs),
        ...     lambda resp: resp.extract_content()
        ... )
        >>> result = await pipeline([Message(role="user", content="Hello")])
    """
    pipeline = Pipeline()
    for step in steps:
        pipeline.add_step(step)
    return pipeline
