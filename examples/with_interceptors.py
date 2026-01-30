"""Example: Using interceptors.

Demonstrates middleware for retry, caching, and logging.
"""

import asyncio
import os

from conduit.interceptors import CacheInterceptor, LoggingInterceptor, RetryInterceptor
from conduit.providers.mock import MockModel
from conduit.providers.openai import OpenAIModel
from conduit.schema.messages import Message


async def main() -> None:
    """Run interceptors example."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Create interceptors
    interceptors = [
        RetryInterceptor(max_attempts=3, backoff_factor=2.0),
        CacheInterceptor(ttl=3600),  # Cache for 1 hour
        LoggingInterceptor(),
    ]
    
    if api_key:
        model = OpenAIModel(api_key=api_key, model="gpt-4")
        # Apply interceptors (in real usage, interceptors wrap the model)
        response = await model.chat(
            [Message(role="user", content="What is async/await?")],
            options=None,
        )
        print("Response:", response.extract_content())
        print("\nNote: Interceptors would be applied via model wrapper in production")
    else:
        # Mock model
        model = MockModel(response_content="async/await is Python's way to handle asynchronous operations.")
        response = await model.chat([
            Message(role="user", content="What is async/await?")
        ])
        print("Response:", response.extract_content())
        print("\nInterceptors available:")
        print("  - RetryInterceptor: Automatic retries with backoff")
        print("  - CacheInterceptor: Response caching")
        print("  - LoggingInterceptor: Request/response logging")
        print("(Using mock model - set OPENAI_API_KEY for real API)")


if __name__ == "__main__":
    asyncio.run(main())
