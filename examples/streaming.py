"""Example: Streaming responses.

Demonstrates how to stream responses token by token.
"""

import asyncio
import os

from conduit.providers.mock import MockModel
from conduit.providers.openai import OpenAIModel
from conduit.schema.messages import Message


async def main() -> None:
    """Run streaming example."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        model = OpenAIModel(api_key=api_key, model="gpt-4")
        print("Streaming response: ", end="", flush=True)
        async for chunk in model.stream([
            Message(role="user", content="Count from 1 to 5")
        ]):
            if hasattr(chunk, "extract_content"):
                content = chunk.extract_content()
                if content:
                    print(content, end="", flush=True)
        print()  # New line after streaming
    else:
        # Mock streaming
        model = MockModel(response_content="1 2 3 4 5")
        print("Streaming response: ", end="", flush=True)
        async for chunk in model.stream([
            Message(role="user", content="Count from 1 to 5")
        ]):
            if hasattr(chunk, "extract_content"):
                content = chunk.extract_content()
                if content:
                    print(content, end="", flush=True)
        print()
        print("(Using mock model - set OPENAI_API_KEY for real streaming)")


if __name__ == "__main__":
    asyncio.run(main())
