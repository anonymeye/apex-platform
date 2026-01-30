"""Example: Memory management strategies.

Demonstrates conversation memory, windowed memory, and summarizing memory.
"""

import asyncio
import os

from conduit.memory import ConversationMemory, SummarizingMemory, WindowedMemory
from conduit.providers.mock import MockModel
from conduit.providers.openai import OpenAIModel
from conduit.schema.messages import Message


async def main() -> None:
    """Run memory management example."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Conversation memory - stores all messages
    conversation_memory = ConversationMemory()
    conversation_memory.add_message(Message(role="user", content="Hello"))
    conversation_memory.add_message(Message(role="assistant", content="Hi there!"))
    conversation_memory.add_message(Message(role="user", content="What is Python?"))
    
    print("Conversation Memory:")
    print(f"  Messages: {len(conversation_memory.get_messages())}")
    
    # Windowed memory - keeps last N tokens
    windowed_memory = WindowedMemory(max_tokens=100)
    windowed_memory.add_message(Message(role="user", content="Hello"))
    windowed_memory.add_message(Message(role="assistant", content="Hi there!"))
    
    print("\nWindowed Memory:")
    print(f"  Messages: {len(windowed_memory.get_messages())}")
    print(f"  Max tokens: {windowed_memory.max_tokens}")
    
    # Summarizing memory - compresses old messages
    if api_key:
        model = OpenAIModel(api_key=api_key, model="gpt-4")
        summarizing_memory = SummarizingMemory(
            model=model,
            max_messages=10,
            summarize_threshold=5,
        )
        summarizing_memory.add_message(Message(role="user", content="Hello"))
        summarizing_memory.add_message(Message(role="assistant", content="Hi!"))
        
        print("\nSummarizing Memory:")
        print(f"  Messages: {len(summarizing_memory.get_messages())}")
        print("(Using real model for summarization)")
    else:
        print("\nSummarizing Memory:")
        print("  (Requires API key for summarization)")
        print("  Compresses old messages into summaries")
    
    print("\nMemory strategies:")
    print("  - ConversationMemory: Store all messages")
    print("  - WindowedMemory: Keep last N tokens")
    print("  - SummarizingMemory: Compress old messages")


if __name__ == "__main__":
    asyncio.run(main())
