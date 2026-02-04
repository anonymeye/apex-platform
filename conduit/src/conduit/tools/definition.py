"""Tool definition for function calling."""

import asyncio
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from conduit.errors import ToolExecutionError
from conduit.errors import ValidationError as ConduitValidationError


class Tool(BaseModel):
    """Tool definition for function calling.

    A Tool wraps a Python function with a Pydantic schema for parameter validation
    and provides conversion to JSON Schema for LLM providers.

    Examples:
        >>> from pydantic import BaseModel
        >>> from typing import Literal
        >>>
        >>> class WeatherParams(BaseModel):
        ...     location: str
        ...     unit: Literal["celsius", "fahrenheit"] = "celsius"
        >>>
        >>> def get_weather(params: WeatherParams) -> dict:
        ...     return {"temp": 72, "condition": "sunny"}
        >>>
        >>> tool = Tool(
        ...     name="get_weather",
        ...     description="Get current weather for a location",
        ...     parameters=WeatherParams,
        ...     fn=get_weather
        ... )
        >>>
        >>> # Convert to JSON Schema for API
        >>> schema = tool.to_json_schema()
        >>>
        >>> # Execute with validated arguments (use await in async context)
        >>> result = await tool.execute({"location": "Tokyo", "unit": "celsius"})
    """

    name: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Tool name (alphanumeric, underscore, hyphen)",
    )
    description: str = Field(..., min_length=1, description="Tool description for the LLM")
    parameters: type[BaseModel] = Field(..., description="Pydantic model for parameter validation")
    fn: Callable[[BaseModel], Any] = Field(..., description="Function to execute")

    model_config = {"arbitrary_types_allowed": True}

    async def execute(self, arguments: dict[str, Any]) -> Any:
        """Execute tool with arguments.

        Supports both sync and async tool functions. If fn returns a coroutine,
        it is awaited; otherwise the value is returned as-is.

        Args:
            arguments: Raw arguments dict from LLM

        Returns:
            Tool execution result (any type)

        Raises:
            ConduitValidationError: If arguments don't match schema
            ToolExecutionError: If tool execution fails

        Examples:
            >>> result = await tool.execute({"location": "Tokyo"})
        """
        # Validate and parse arguments
        try:
            params = self.parameters(**arguments)
        except ValidationError as e:
            raise ConduitValidationError(f"Invalid arguments for tool '{self.name}': {e}") from e

        # Execute function (sync or async)
        try:
            raw = self.fn(params)
            if asyncio.iscoroutine(raw):
                return await raw
            return raw
        except Exception as e:
            raise ToolExecutionError(
                f"Error executing tool '{self.name}': {str(e)}", tool_name=self.name
            ) from e

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to OpenAI tool format (JSON Schema).

        Returns:
            Dict in OpenAI tool calling format:
            {
                "type": "function",
                "function": {
                    "name": "...",
                    "description": "...",
                    "parameters": {...}  # JSON Schema
                }
            }

        Examples:
            >>> schema = tool.to_json_schema()
            >>> # Use in ChatOptions.tools
            >>> opts = ChatOptions(tools=[schema])
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters.model_json_schema(),
            },
        }
