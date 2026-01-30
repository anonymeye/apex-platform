"""JSON Schema conversion utilities for tools."""

from typing import Any

from pydantic import BaseModel


def pydantic_to_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Convert Pydantic model to JSON Schema.

    This is a convenience function that wraps Pydantic's built-in
    model_json_schema() method. It's provided for consistency and
    potential future extensions.

    Args:
        model: Pydantic model class

    Returns:
        JSON Schema dict

    Examples:
        >>> from pydantic import BaseModel
        >>>
        >>> class Params(BaseModel):
        ...     name: str
        ...     age: int
        >>>
        >>> schema = pydantic_to_json_schema(Params)
    """
    return model.model_json_schema()
