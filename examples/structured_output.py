"""Example: Structured output extraction.

Demonstrates extracting structured data from model responses.
"""

import asyncio
import os

from conduit.providers.mock import MockModel
from conduit.providers.openai import OpenAIModel
from conduit.schema.messages import Message
from conduit.structured import classify, extract_structured
from pydantic import BaseModel


# Define structured schema
class Person(BaseModel):
    """Person information."""
    name: str
    age: int
    email: str


async def main() -> None:
    """Run structured output example."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        model = OpenAIModel(api_key=api_key, model="gpt-4")
        # Extract structured data
        text = "John is 30 years old. His email is john@example.com."
        person = await extract_structured(model, text, Person)
        print("Extracted person:", person)
        
        # Classify text
        category = await classify(
            model,
            text="This product is amazing!",
            categories=["positive", "negative", "neutral"],
        )
        print("Classification:", category)
    else:
        # Mock structured extraction
        model = MockModel(response_content='{"name": "John", "age": 30, "email": "john@example.com"}')
        
        # Simulate extraction
        text = "John is 30 years old. His email is john@example.com."
        print(f"Extracting from: {text}")
        print("(Using mock model - set OPENAI_API_KEY for real extraction)")
        print("\nAvailable functions:")
        print("  - extract_structured(): Extract Pydantic models from text")
        print("  - extract_json(): Extract JSON objects")
        print("  - extract_list(): Extract lists")
        print("  - classify(): Classify text into categories")
        print("  - extract_key_value_pairs(): Extract key-value pairs")


if __name__ == "__main__":
    asyncio.run(main())
