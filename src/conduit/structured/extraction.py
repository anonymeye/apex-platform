"""Data extraction utilities for parsing LLM responses."""

import re
from typing import Any

from conduit.schema.responses import Response


def extract_json(response: Response) -> dict[str, Any] | list[Any]:
    """Extract JSON from a response.

    Args:
        response: Response from the model

    Returns:
        Parsed JSON (dict or list)

    Raises:
        ValueError: If JSON cannot be parsed

    Examples:
        >>> response = Response(
        ...     content='{"key": "value"}',
        ...     usage=Usage(input_tokens=10, output_tokens=5)
        ... )
        >>> data = extract_json(response)
        >>> assert data["key"] == "value"
    """
    import json

    from conduit.structured.output import _extract_json_from_text

    content = response.extract_content()
    json_str = _extract_json_from_text(content)

    try:
        parsed: dict[str, Any] | list[Any] = json.loads(json_str)
        return parsed
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}") from e


def extract_list(response: Response, *, pattern: str | None = None) -> list[str]:
    """Extract a list of items from a response.

    Args:
        response: Response from the model
        pattern: Optional regex pattern to match items. If None, uses bullet points.

    Returns:
        List of extracted items

    Examples:
        >>> response = Response(
        ...     content="- Apple\\n- Banana\\n- Cherry",
        ...     usage=Usage(input_tokens=10, output_tokens=5)
        ... )
        >>> items = extract_list(response)
        >>> assert "Apple" in items
    """
    content = response.extract_content()

    if pattern:
        matches = re.findall(pattern, content, re.MULTILINE)
        return [m.strip() if isinstance(m, str) else m[0].strip() for m in matches]

    # Default: extract bullet points
    items: list[str] = []
    for line in content.split("\n"):
        line = line.strip()
        # Match various bullet formats: -, *, •, 1., etc.
        if re.match(r"^[-*•]\s+", line):
            items.append(re.sub(r"^[-*•]\s+", "", line))
        elif re.match(r"^\d+\.\s+", line):
            items.append(re.sub(r"^\d+\.\s+", "", line))

    return items


def extract_key_value_pairs(
    response: Response, *, separator: str = ":"
) -> dict[str, str]:
    """Extract key-value pairs from a response.

    Args:
        response: Response from the model
        separator: Separator between key and value (default: ":")

    Returns:
        Dictionary of key-value pairs

    Examples:
        >>> response = Response(
        ...     content="Name: Alice\\nAge: 30\\nCity: New York",
        ...     usage=Usage(input_tokens=10, output_tokens=5)
        ... )
        >>> pairs = extract_key_value_pairs(response)
        >>> assert pairs["Name"] == "Alice"
    """
    content = response.extract_content()
    pairs: dict[str, str] = {}

    for line in content.split("\n"):
        line = line.strip()
        if separator in line:
            parts = line.split(separator, 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                pairs[key] = value

    return pairs


def extract_code_blocks(
    response: Response, *, language: str | None = None
) -> list[tuple[str, str]]:
    """Extract code blocks from a response.

    Args:
        response: Response from the model
        language: Optional language filter (e.g., "python", "javascript")

    Returns:
        List of (language, code) tuples

    Examples:
        >>> response = Response(
        ...     content='```python\\nprint("Hello")\\n```',
        ...     usage=Usage(input_tokens=10, output_tokens=5)
        ... )
        >>> blocks = extract_code_blocks(response)
        >>> assert blocks[0][0] == "python"
        >>> assert "print" in blocks[0][1]
    """
    content = response.extract_content()
    blocks: list[tuple[str, str]] = []

    # Pattern: ```language\ncode\n```
    pattern = r"```(\w+)?\n(.*?)```"
    matches = re.findall(pattern, content, re.DOTALL)

    for match in matches:
        block_lang = match[0] if match[0] else ""
        code = match[1].strip()

        if language is None or block_lang == language:
            blocks.append((block_lang, code))

    return blocks


def classify(
    response: Response, categories: list[str], *, default: str | None = None
) -> str:
    """Classify response content into one of the given categories.

    This is a simple classification that looks for category names in the response.

    Args:
        response: Response from the model
        categories: List of possible categories
        default: Default category if none found (if None, raises ValueError)

    Returns:
        Category name

    Raises:
        ValueError: If no category found and no default provided

    Examples:
        >>> response = Response(
        ...     content="This is a positive review",
        ...     usage=Usage(input_tokens=10, output_tokens=5)
        ... )
        >>> category = classify(response, ["positive", "negative", "neutral"])
        >>> assert category == "positive"
    """
    content = response.extract_content().lower()

    for category in categories:
        if category.lower() in content:
            return category

    if default:
        return default

    raise ValueError(f"Could not classify response into any of: {categories}")
