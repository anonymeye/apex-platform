# API Reference

## Providers

### OpenAIModel

```python
from conduit.providers.openai import OpenAIModel

async with OpenAIModel(api_key="...", model="gpt-4") as model:
    response = await model.chat(messages: list[Message], ...)
    async for chunk in model.stream(messages: list[Message], ...):
        ...
```

### AnthropicModel

```python
from conduit.providers.anthropic import AnthropicModel

async with AnthropicModel(api_key="...", model="claude-3-opus") as model:
    response = await model.chat(messages: list[Message], ...)
```

### GroqModel

```python
from conduit.providers.groq import GroqModel

async with GroqModel(api_key="...", model="llama-3-70b") as model:
    response = await model.chat(messages: list[Message], ...)
```

## Schema

### Message

```python
from conduit.schema.messages import Message

Message(role="user", content="Hello")
Message(role="assistant", content="Hi there")
Message(role="system", content="You are helpful")
```

### Response

```python
from conduit.schema.responses import Response

response: Response = await model.chat(messages)
content = response.extract_content()
usage = response.usage
tool_calls = response.tool_calls
```

### ChatOptions

```python
from conduit.schema.options import ChatOptions

options = ChatOptions(
    temperature=0.7,
    max_tokens=1000,
    top_p=0.9,
)
```

## Tools

### Tool

```python
from conduit.tools import Tool
from pydantic import BaseModel

class Params(BaseModel):
    query: str

def search(query: str) -> str:
    return f"Results for {query}"

tool = Tool(
    name="search",
    description="Search the web",
    params=Params,
    func=search,
)
```

## Agents

### make_agent

```python
from conduit.agent import make_agent

agent = make_agent(
    model=model,
    tools=[tool1, tool2],
    system_message="You are helpful",
    max_iterations=10,
)

result = await agent("User message")
```

### tool_loop

```python
from conduit.agent import tool_loop

result = await tool_loop(
    model=model,
    messages=[Message(role="user", content="...")],
    tools=[tool1, tool2],
    max_iterations=10,
)
```

## Interceptors

### RetryInterceptor

```python
from conduit.interceptors import RetryInterceptor

interceptor = RetryInterceptor(
    max_attempts=3,
    backoff_factor=2.0,
)
```

### CacheInterceptor

```python
from conduit.interceptors import CacheInterceptor

interceptor = CacheInterceptor(ttl=3600)
```

### LoggingInterceptor

```python
from conduit.interceptors import LoggingInterceptor

interceptor = LoggingInterceptor()
```

## RAG

### RAGChain

```python
from conduit.rag import RAGChain, MemoryVectorStore, EmbeddingModel

store = MemoryVectorStore()
embedding_model = EmbeddingModel(model)
chain = RAGChain(
    model=chat_model,
    retriever=VectorRetriever(store, embedding_model),
)

response = await chain.query("What is Python?")
```

### Text Splitters

```python
from conduit.rag import RecursiveSplitter, CharacterSplitter

splitter = RecursiveSplitter(chunk_size=1000, chunk_overlap=200)
documents = splitter.split(text)
```

## Memory

### ConversationMemory

```python
from conduit.memory import ConversationMemory

memory = ConversationMemory()
memory.add_message(Message(role="user", content="Hi"))
messages = memory.get_messages()
```

### WindowedMemory

```python
from conduit.memory import WindowedMemory

memory = WindowedMemory(max_tokens=4000, tokenizer=tokenizer)
```

## Structured Output

### extract_structured

```python
from conduit.structured import extract_structured
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int

person = await extract_structured(model, "Extract: John is 30", Person)
```

### classify

```python
from conduit.structured import classify

category = await classify(
    model,
    text="This is great!",
    categories=["positive", "negative", "neutral"],
)
```
