"""Tests for structured output and extraction."""

import pytest

from conduit.schema.responses import Response, Usage
from conduit.structured import (
    classify,
    extract_code_blocks,
    extract_json,
    extract_key_value_pairs,
    extract_list,
    extract_structured,
)


def test_extract_structured():
    """Test extract_structured with valid JSON."""
    from pydantic import BaseModel

    class Person(BaseModel):
        name: str
        age: int

    response = Response(
        content='{"name": "Alice", "age": 30}',
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    person = extract_structured(response, Person)
    assert person.name == "Alice"
    assert person.age == 30


def test_extract_structured_with_code_block():
    """Test extract_structured extracts JSON from code blocks."""
    from pydantic import BaseModel

    class Person(BaseModel):
        name: str
        age: int

    response = Response(
        content='```json\n{"name": "Bob", "age": 25}\n```',
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    person = extract_structured(response, Person)
    assert person.name == "Bob"
    assert person.age == 25


def test_extract_structured_invalid_json():
    """Test extract_structured raises error on invalid JSON."""
    from pydantic import BaseModel

    class Person(BaseModel):
        name: str
        age: int

    response = Response(
        content="This is not JSON",
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    with pytest.raises(Exception):  # Should raise ValidationError
        extract_structured(response, Person)


def test_extract_json():
    """Test extract_json."""
    response = Response(
        content='{"key": "value", "number": 42}',
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    data = extract_json(response)
    assert data["key"] == "value"
    assert data["number"] == 42


def test_extract_json_list():
    """Test extract_json with array."""
    response = Response(
        content='[1, 2, 3, "four"]',
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    data = extract_json(response)
    assert isinstance(data, list)
    assert data == [1, 2, 3, "four"]


def test_extract_list():
    """Test extract_list with bullet points."""
    response = Response(
        content="- Apple\n- Banana\n- Cherry",
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    items = extract_list(response)
    assert "Apple" in items
    assert "Banana" in items
    assert "Cherry" in items


def test_extract_list_numbered():
    """Test extract_list with numbered list."""
    response = Response(
        content="1. First item\n2. Second item\n3. Third item",
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    items = extract_list(response)
    assert len(items) == 3
    assert "First item" in items


def test_extract_key_value_pairs():
    """Test extract_key_value_pairs."""
    response = Response(
        content="Name: Alice\nAge: 30\nCity: New York",
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    pairs = extract_key_value_pairs(response)
    assert pairs["Name"] == "Alice"
    assert pairs["Age"] == "30"
    assert pairs["City"] == "New York"


def test_extract_code_blocks():
    """Test extract_code_blocks."""
    response = Response(
        content='```python\nprint("Hello")\n```\n```javascript\nconsole.log("Hi")\n```',
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    blocks = extract_code_blocks(response)
    assert len(blocks) == 2
    assert blocks[0][0] == "python"
    assert "print" in blocks[0][1]
    assert blocks[1][0] == "javascript"
    assert "console.log" in blocks[1][1]


def test_extract_code_blocks_filtered():
    """Test extract_code_blocks with language filter."""
    response = Response(
        content='```python\nprint("Hello")\n```\n```javascript\nconsole.log("Hi")\n```',
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    blocks = extract_code_blocks(response, language="python")
    assert len(blocks) == 1
    assert blocks[0][0] == "python"


def test_classify():
    """Test classify function."""
    response = Response(
        content="This is a positive review of the product",
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    category = classify(response, ["positive", "negative", "neutral"])
    assert category == "positive"


def test_classify_with_default():
    """Test classify with default category."""
    response = Response(
        content="This doesn't match any category",
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    category = classify(response, ["positive", "negative"], default="neutral")
    assert category == "neutral"


def test_classify_no_match():
    """Test classify raises error when no match found."""
    response = Response(
        content="This doesn't match",
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    with pytest.raises(ValueError):
        classify(response, ["positive", "negative"])
