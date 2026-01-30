# Quick Start Guide

## Basic Chat

```python
from conduit.providers.openai import OpenAIModel
from conduit.schema.messages import Message

async with OpenAIModel(api_key="sk-...", model="gpt-4") as model:
    response = await model.chat([
        Message(role="user", content="What is Python?")
    ])
    print(response.extract_content())
```

## Streaming

```python
async with OpenAIModel(api_key="sk-...", model="gpt-4") as model:
    async for chunk in model.stream([
        Message(role="user", content="Tell me a story")
    ]):
        print(chunk.extract_content(), end="", flush=True)
```

## Tool Calling

```python
from conduit.tools import Tool
from pydantic import BaseModel

class WeatherParams(BaseModel):
    location: str

async def get_weather(location: str) -> str:
    return f"Weather in {location}: 72°F, sunny"

weather_tool = Tool(
    name="get_weather",
    description="Get weather for a location",
    params=WeatherParams,
    func=get_weather,
)

async with OpenAIModel(api_key="sk-...", model="gpt-4") as model:
    response = await model.chat(
        [Message(role="user", content="What's the weather in Tokyo?")],
        tools=[weather_tool],
    )
    print(response.extract_content())
```

## Agent Loop

```python
from conduit.agent import make_agent

async with OpenAIModel(api_key="sk-...", model="gpt-4") as model:
    agent = make_agent(
        model=model,
        tools=[weather_tool],
        system_message="You are a helpful assistant.",
        max_iterations=5,
    )
    result = await agent("What's the weather in Paris and London?")
    print(result.response.extract_content())
```

## With Interceptors

```python
from conduit.interceptors import RetryInterceptor, CacheInterceptor

interceptors = [
    RetryInterceptor(max_attempts=3),
    CacheInterceptor(ttl=3600),
]

async with OpenAIModel(api_key="sk-...", model="gpt-4") as model:
    response = await model.chat(
        [Message(role="user", content="Hello!")],
        interceptors=interceptors,
    )
```

## Multiple Providers

```python
from conduit.providers.anthropic import AnthropicModel
from conduit.providers.groq import GroqModel

# Same interface, different providers
async with AnthropicModel(api_key="sk-...", model="claude-3-opus") as model:
    response = await model.chat([Message(role="user", content="Hi")])
```
