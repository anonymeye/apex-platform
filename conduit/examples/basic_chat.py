"""Example: Basic chat interaction.

Demonstrates simple chat completion with a model.
"""

import asyncio
import os

from conduit.providers.mock import MockModel
from conduit.providers.openai import OpenAIModel
from conduit.schema.messages import Message


async def main() -> None:
    """Run basic chat example."""
    # Use mock model if no API key, otherwise use OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        model = OpenAIModel(api_key=api_key, model="gpt-4")
        response = await model.chat([
            Message(role="user", content="What is Python?")
        ])
        print("Response:", response.extract_content())
        print(f"Usage: {response.usage.input_tokens} input, {response.usage.output_tokens} output tokens")
    else:
        # Mock model for demonstration
        model = MockModel(response_content="Python is a high-level programming language.")
        response = await model.chat([
            Message(role="user", content="What is Python?")
        ])
        print("Response:", response.extract_content())
        print("(Using mock model - set OPENAI_API_KEY for real API)")


if __name__ == "__main__":
    asyncio.run(main())
