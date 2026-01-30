# Conduit Python Port - Quick Reference

> **Companion to**: [PYTHON_PORT_GUIDE.md](./PYTHON_PORT_GUIDE.md)
> 
> **Purpose**: Quick lookup for common patterns and decisions

---

## 🎯 Core Decisions Summary

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Min Python Version** | 3.11+ | Modern type hints, better async |
| **Validation** | Pydantic v2 | Fast, excellent DX, JSON schema |
| **HTTP Client** | httpx | Async, modern, HTTP/2 support |
| **Async Pattern** | AsyncIterator | More Pythonic than channels |
| **Type Checking** | mypy strict | Catch errors early |
| **Formatting** | black + ruff | Industry standard |
| **Testing** | pytest + pytest-asyncio | De facto standard |
| **Logging** | structlog | Structured, async-friendly |

---

## 📦 Package Name & Structure

```
Package Name: conduit-py (or just conduit if available)
Import: import conduit
```

```python
# Public API
from conduit import (
    # Core
    ChatModel, Embeddable,
    Message, Response, ChatOptions,
    chat, stream, embed,
    
    # Providers
    OpenAIModel, AnthropicModel, GroqModel,
    
    # Tools & Agents
    Tool, make_agent, tool_loop,
    
    # Interceptors
    execute_interceptors,
    RetryInterceptor, LoggingInterceptor, CacheInterceptor,
    
    # RAG
    RAGChain, VectorStore, Retriever,
    CharacterSplitter, RecursiveSplitter,
    
    # Structured
    extract_with_schema, classify,
    
    # Errors
    ConduitError, ProviderError, ValidationError,
)
```

---

## 🔄 Clojure → Python Translation Table

### Data Structures

| Clojure | Python | Example |
|---------|--------|---------|
| `{:role :user :content "Hi"}` | `Message(role="user", content="Hi")` | Pydantic model |
| `[:map [:location :string]]` | `class Params(BaseModel): location: str` | Schema |
| `[:enum "a" "b"]` | `Literal["a", "b"]` | Enum |
| `{:optional true}` | `field: str \| None = None` | Optional |
| `(atom {})` | `asyncio.Lock() + dict` | Mutable state |

### Functions

| Clojure | Python | Notes |
|---------|--------|-------|
| `(defn f [x] ...)` | `def f(x: T) -> R: ...` | Add types |
| `(defn f [x & opts] ...)` | `def f(x: T, *, opts: O = None): ...` | Keyword-only |
| `(fn [x] ...)` | `lambda x: ...` or `def` | Prefer def |
| `(comp f g h)` | `lambda x: f(g(h(x)))` | Or decorator |
| `(-> x f g h)` | `h(g(f(x)))` | Or method chain |

### Async

| Clojure | Python | Notes |
|---------|--------|-------|
| `(go ...)` | `async def ...` | Async function |
| `(<! ch)` | `async for x in ch:` | Async iteration |
| `(>! ch x)` | `yield x` | In async generator |
| `(go-loop [] ... (recur))` | `async for:` or `while:` | Loop |
| `core.async/chan` | `AsyncIterator` | Use generator |

### Protocols

| Clojure | Python | Notes |
|---------|--------|-------|
| `(defprotocol P ...)` | `class P(ABC): ...` | Abstract base |
| `(defrecord R [] P ...)` | `class R(P): ...` | Implementation |
| `(extend-protocol ...)` | Implement in class | No monkey-patch |

---

## 🎨 Code Templates

### 1. Basic Chat

```python
from conduit import OpenAIModel, Message

async def main():
    async with OpenAIModel(api_key="sk-...") as model:
        response = await model.chat([
            Message(role="user", content="Hello!")
        ])
        print(response.content)
```

### 2. Streaming

```python
async def main():
    async with OpenAIModel(api_key="sk-...") as model:
        async for event in model.stream([
            Message(role="user", content="Tell me a story")
        ]):
            if event.type == "content_delta":
                print(event.text, end="", flush=True)
```

### 3. Tool Calling

```python
from pydantic import BaseModel
from conduit import Tool, make_agent

class WeatherParams(BaseModel):
    location: str

def get_weather(params: WeatherParams) -> dict:
    return {"temp": 72, "condition": "sunny"}

weather_tool = Tool(
    name="get_weather",
    description="Get weather for a location",
    parameters=WeatherParams,
    fn=get_weather
)

agent = make_agent(model, [weather_tool])
result = await agent("What's the weather in Tokyo?")
```

### 4. With Interceptors

```python
from conduit import execute_interceptors, RetryInterceptor, LoggingInterceptor

response = await execute_interceptors(
    model,
    messages,
    [
        RetryInterceptor(max_attempts=3),
        LoggingInterceptor(level="info")
    ]
)
```

### 5. RAG Pipeline

```python
from conduit.rag import RAGChain, MemoryVectorStore, VectorRetriever
from conduit.rag.splitters import RecursiveSplitter

# Split documents
splitter = RecursiveSplitter(chunk_size=500)
chunks = splitter.split(text)

# Create embeddings and store
store = MemoryVectorStore()
embeddings = await embed_model.embed([c.content for c in chunks])
store.add_documents(chunks, embeddings)

# Create retriever
retriever = VectorRetriever(store, embed_model)

# Create RAG chain
rag = RAGChain(model=model, retriever=retriever, k=5)

# Query
result = await rag("What is machine learning?")
print(result["answer"])
```

---

## 🏗️ File Templates

### Provider Template

```python
# src/conduit/providers/my_provider.py
"""My Provider implementation."""

import httpx
from typing import AsyncIterator
from conduit.core.protocols import ChatModel
from conduit.schema.messages import Message
from conduit.schema.responses import Response, StreamEvent
from conduit.schema.options import ChatOptions
from conduit.core.models import ModelInfo, Capabilities


class MyProviderModel(ChatModel):
    """My Provider model implementation."""
    
    def __init__(self, *, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self._client: httpx.AsyncClient | None = None
    
    async def chat(
        self,
        messages: list[Message],
        options: ChatOptions | None = None
    ) -> Response:
        # Implementation
        ...
    
    async def stream(
        self,
        messages: list[Message],
        options: ChatOptions | None = None
    ) -> AsyncIterator[StreamEvent]:
        # Implementation
        ...
    
    def model_info(self) -> ModelInfo:
        return ModelInfo(
            provider="my_provider",
            model=self.model,
            capabilities=Capabilities(...)
        )
```

### Interceptor Template

```python
# src/conduit/interceptors/my_interceptor.py
"""My custom interceptor."""

from dataclasses import dataclass
from conduit.interceptors.base import Interceptor, Context


@dataclass
class MyInterceptor:
    """My interceptor description."""
    
    param: str
    
    async def enter(self, ctx: Context) -> Context:
        # Before model call
        return ctx
    
    async def leave(self, ctx: Context) -> Context:
        # After model call
        return ctx
    
    async def error(self, ctx: Context, error: Exception) -> Context:
        # On error
        return ctx
```

### Test Template

```python
# tests/unit/test_my_module.py
"""Tests for my module."""

import pytest
from conduit.my_module import MyClass


class TestMyClass:
    """Test suite for MyClass."""
    
    @pytest.fixture
    def instance(self):
        """Create test instance."""
        return MyClass(param="value")
    
    @pytest.mark.asyncio
    async def test_method(self, instance):
        """Test method behavior."""
        result = await instance.method()
        assert result == expected
```

---

## 🔧 Configuration Files

### pyproject.toml (minimal)

```toml
[tool.poetry]
name = "conduit-py"
version = "0.1.0"
description = "Simple, functional LLM orchestration for Python"
authors = ["Your Name <you@example.com>"]
license = "MIT"
readme = "README.md"
packages = [{include = "conduit", from = "src"}]

[tool.poetry.dependencies]
python = "^3.11"
pydantic = "^2.0"
httpx = "^0.27"
numpy = "^1.26"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
pytest-cov = "^4.1"
mypy = "^1.8"
ruff = "^0.1"
black = "^24.0"

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "B", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### .gitignore

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.env
.DS_Store
```

---

## 📝 Docstring Template

```python
async def function_name(
    param1: Type1,
    param2: Type2,
    *,
    optional: Type3 | None = None
) -> ReturnType:
    """Short one-line description.
    
    Longer description with more details about what this function does,
    when to use it, and any important considerations.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        optional: Description of optional parameter
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param1 is invalid
        RuntimeError: When operation fails
    
    Examples:
        Basic usage:
        
        >>> result = await function_name("value1", "value2")
        >>> print(result)
        
        With optional parameter:
        
        >>> result = await function_name(
        ...     "value1",
        ...     "value2",
        ...     optional="value3"
        ... )
    
    See Also:
        - related_function: Related functionality
        - OtherClass: Related class
    
    Note:
        Any important notes or warnings.
    """
    ...
```

---

## ⚠️ Common Mistakes to Avoid

### ❌ DON'T

```python
# ❌ Blocking I/O in async function
async def chat(self, messages):
    return requests.post(url, json=data)  # WRONG!

# ❌ Missing type hints
def process(data):
    return data.upper()

# ❌ Bare except
try:
    result = await model.chat(messages)
except:
    print("Error")

# ❌ Plain dict instead of Pydantic
def create_message(role, content):
    return {"role": role, "content": content}

# ❌ Not closing resources
client = httpx.AsyncClient()
response = await client.get(url)
# Forgot to close!
```

### ✅ DO

```python
# ✅ Async I/O
async def chat(self, messages: list[Message]) -> Response:
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return parse_response(response)

# ✅ Complete type hints
def process(data: str) -> str:
    return data.upper()

# ✅ Specific exceptions
try:
    result = await model.chat(messages)
except httpx.HTTPError as e:
    raise ProviderError(f"API error: {e}") from e

# ✅ Pydantic models
def create_message(role: str, content: str) -> Message:
    return Message(role=role, content=content)

# ✅ Context manager
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

---

## 🧪 Testing Patterns

### Mock HTTP Responses

```python
@pytest.mark.asyncio
async def test_chat(httpx_mock):
    """Test chat with mocked HTTP."""
    httpx_mock.add_response(
        url="https://api.provider.com/chat",
        json={"response": "Hello!"}
    )
    
    model = MyModel(api_key="test")
    response = await model.chat([Message(role="user", content="Hi")])
    
    assert response.content == "Hello!"
```

### Async Fixtures

```python
@pytest.fixture
async def model():
    """Create test model."""
    async with OpenAIModel(api_key="test") as m:
        yield m
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
])
def test_upper(input, expected):
    assert input.upper() == expected
```

---

## 📊 Performance Tips

1. **Use connection pooling**: httpx.AsyncClient reuses connections
2. **Batch operations**: Embed multiple texts at once
3. **Stream when possible**: Lower latency for long responses
4. **Cache embeddings**: Expensive to compute
5. **Use async context managers**: Ensures cleanup
6. **Limit concurrency**: Use `asyncio.Semaphore` for rate limiting

```python
# Good: Reuse client
async with httpx.AsyncClient() as client:
    for _ in range(100):
        await client.get(url)

# Bad: Create new client each time
for _ in range(100):
    async with httpx.AsyncClient() as client:
        await client.get(url)
```

---

## 🔍 Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Pydantic Models

```python
# Print model as JSON
print(message.model_dump_json(indent=2))

# Validate data
try:
    Message(**data)
except ValidationError as e:
    print(e.json())
```

### Check Type Hints

```bash
mypy src/conduit --strict
```

---

## 📚 Key Differences from Clojure Version

| Aspect | Clojure | Python |
|--------|---------|--------|
| **Data** | Plain maps | Pydantic models |
| **Async** | core.async channels | AsyncIterator |
| **Validation** | Malli | Pydantic |
| **Composition** | `comp`, `->`, `->>` | Functions, methods |
| **State** | Atoms | Locks + dicts |
| **Protocols** | defprotocol | ABC |
| **Records** | defrecord | dataclass/BaseModel |
| **Errors** | ex-info | Custom exceptions |

---

## 🎯 Priority Order for Implementation

1. **Core** (protocols, schemas, errors)
2. **One Provider** (OpenAI recommended)
3. **Basic Interceptors** (retry, logging)
4. **Tools** (definition, execution)
5. **Agent Loop** (basic tool loop)
6. **More Providers** (Anthropic, Groq)
7. **RAG** (splitters, stores, retriever)
8. **Advanced Features** (memory, workflows)

---

## 📖 Essential Reading

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [httpx Documentation](https://www.python-httpx.org/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [Type Hints PEP 484](https://peps.python.org/pep-0484/)
- [Python Protocols PEP 544](https://peps.python.org/pep-0544/)

---

**For complete details, see [PYTHON_PORT_GUIDE.md](./PYTHON_PORT_GUIDE.md)**
