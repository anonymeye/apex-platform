"""Structured output utilities for extracting typed data from LLM responses."""

import json
from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel, ValidationError

from conduit.errors import ValidationError as ConduitValidationError
from conduit.schema.responses import Response

if TYPE_CHECKING:
    from conduit.core.protocols import ChatModel
    from conduit.schema.messages import Message
    from conduit.schema.options import ChatOptions

T = TypeVar("T", bound=BaseModel)


def extract_structured(
    response: Response, schema: type[T], *, strict: bool = True
) -> T:
    """Extract structured data from a response using a Pydantic schema.

    This function attempts to parse the response content as JSON and validate
    it against the provided Pydantic schema.

    Args:
        response: Response from the model
        schema: Pydantic model class to validate against
        strict: If True, raise error on validation failure. If False, return partial data.

    Returns:
        Validated instance of the schema

    Raises:
        ConduitValidationError: If content cannot be parsed or validated

    Examples:
        >>> from pydantic import BaseModel
        >>> from conduit.schema.responses import Response, Usage
        >>>
        >>> class Person(BaseModel):
        ...     name: str
        ...     age: int
        >>>
        >>> response = Response(
        ...     content='{"name": "Alice", "age": 30}',
        ...     usage=Usage(input_tokens=10, output_tokens=5)
        ... )
        >>> person = extract_structured(response, Person)
        >>> assert person.name == "Alice"
        >>> assert person.age == 30
    """
    content = response.extract_content()

    # Try to extract JSON from the content
    # Look for JSON in code blocks or plain JSON
    json_str = _extract_json_from_text(content)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ConduitValidationError(f"Failed to parse JSON from response: {e}") from e

    try:
        return schema.model_validate(data)
    except ValidationError as e:
        if strict:
            raise ConduitValidationError(f"Validation failed: {e}") from e
        # In non-strict mode, try to create partial object
        # This is a best-effort approach
        try:
            return schema.model_validate(data, strict=False)
        except Exception:
            raise ConduitValidationError(f"Validation failed: {e}") from e


def _extract_json_from_text(text: str) -> str:
    """Extract JSON from text, handling code blocks and plain JSON.

    Args:
        text: Text that may contain JSON

    Returns:
        JSON string
    """
    text = text.strip()

    # Check if it's already valid JSON
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    # Look for JSON in code blocks (```json ... ```)
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()

    # Look for JSON in generic code blocks (``` ... ```)
    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end != -1:
            candidate = text[start:end].strip()
            # Try to parse it
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

    # Look for JSON object/array boundaries
    # Find first { or [ and last } or ]
    json_start = -1
    json_end = -1

    for i, char in enumerate(text):
        if char in "{[":
            json_start = i
            break

    for i in range(len(text) - 1, -1, -1):
        if text[i] in "}]":
            json_end = i + 1
            break

    if json_start != -1 and json_end != -1 and json_end > json_start:
        candidate = text[json_start:json_end]
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass

    # Last resort: return the text as-is and let JSON parser handle it
    return text


async def with_structured_output(
    model: "ChatModel",
    messages: list["Message"],
    schema: type[T],
    *,
    options: "ChatOptions | None" = None,
    strict: bool = True,
) -> T:
    """Call model and extract structured output.

    This is a convenience function that:
    1. Calls the model with messages
    2. Extracts structured data from the response
    3. Validates against the schema

    Args:
        model: ChatModel instance
        messages: Messages to send
        schema: Pydantic model class
        options: Optional chat options
        strict: If True, raise error on validation failure

    Returns:
        Validated instance of the schema

    Examples:
        >>> from pydantic import BaseModel
        >>> from conduit.providers.openai import OpenAIModel
        >>>
        >>> class Person(BaseModel):
        ...     name: str
        ...     age: int
        >>>
        >>> async with OpenAIModel(api_key="sk-...") as model:
        ...     person = await with_structured_output(
        ...         model,
        ...         [Message(role="user", content="Extract: Alice is 30 years old")],
        ...         Person
        ...     )
    """
    from conduit.schema.options import ChatOptions

    # Set response_format to JSON if supported
    opts = options or ChatOptions(temperature=None, max_tokens=None, top_p=None)
    if hasattr(opts, "response_format"):
        opts.response_format = {"type": "json_object"}

    response = await model.chat(messages, opts)
    return extract_structured(response, schema, strict=strict)
