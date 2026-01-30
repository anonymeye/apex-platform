"""Example: Using multiple providers.

Demonstrates switching between different LLM providers.
"""

import asyncio
import os

from conduit.providers.anthropic import AnthropicModel
from conduit.providers.groq import GroqModel
from conduit.providers.mock import MockModel
from conduit.providers.openai import OpenAIModel
from conduit.schema.messages import Message


async def chat_with_model(model, provider_name: str) -> None:
    """Chat with a model and print response."""
    try:
        if hasattr(model, "__aenter__"):
            async with model as m:
                response = await m.chat([
                    Message(role="user", content="Say hello in one sentence")
                ])
                print(f"{provider_name}: {response.extract_content()}")
        else:
            response = await model.chat([
                Message(role="user", content="Say hello in one sentence")
            ])
            print(f"{provider_name}: {response.extract_content()}")
    except Exception as e:
        print(f"{provider_name}: Error - {e}")


async def main() -> None:
    """Run multi-provider example."""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    print("Multi-Provider Example\n")
    
    # OpenAI
    if openai_key:
        await chat_with_model(
            OpenAIModel(api_key=openai_key, model="gpt-4"),
            "OpenAI"
        )
    else:
        print("OpenAI: (Set OPENAI_API_KEY to use)")
    
    # Anthropic
    if anthropic_key:
        await chat_with_model(
            AnthropicModel(api_key=anthropic_key, model="claude-3-opus"),
            "Anthropic"
        )
    else:
        print("Anthropic: (Set ANTHROPIC_API_KEY to use)")
    
    # Groq
    if groq_key:
        await chat_with_model(
            GroqModel(api_key=groq_key, model="llama-3-70b"),
            "Groq"
        )
    else:
        print("Groq: (Set GROQ_API_KEY to use)")
    
    # Mock (always available)
    await chat_with_model(
        MockModel(response_content="Hello from mock model!"),
        "Mock"
    )
    
    print("\nAll providers share the same ChatModel interface.")


if __name__ == "__main__":
    asyncio.run(main())
