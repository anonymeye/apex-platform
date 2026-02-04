# Conduit Python Port Implementation Guide

> **Target Audience**: AI coding agents and developers implementing Conduit in Python
> 
> **Purpose**: Comprehensive guidelines for porting the Clojure-based Conduit library to Python while maintaining its philosophy and improving upon it with Python best practices.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Core Philosophy & Principles](#core-philosophy--principles)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Implementation Guidelines by Module](#implementation-guidelines-by-module)
6. [Code Style & Standards](#code-style--standards)
7. [Testing Requirements](#testing-requirements)
8. [Documentation Standards](#documentation-standards)
9. [Migration Mapping Reference](#migration-mapping-reference)
10. [Common Patterns & Recipes](#common-patterns--recipes)

---

## Project Overview

### What is Conduit?

Conduit is a **simple, functional LLM orchestration library** that provides:
- Unified interface to multiple LLM providers (OpenAI, Anthropic, Groq, etc.)
- Tool calling and autonomous agents
- Streaming responses
- RAG (Retrieval-Augmented Generation) pipelines
- Interceptor-based middleware
- Memory management
- Workflow orchestration

### Core Differentiators

Unlike LangChain, Conduit is:
- **Data-first**: Plain data structures over complex class hierarchies
- **Explicit**: No hidden state or magic
- **Composable**: Standard language features for composition
- **Type-safe**: Full type hints and validation
- **Debuggable**: Easy to inspect and understand

---

## Core Philosophy & Principles

### 1. Data-First Design

**Principle**: Use simple data structures (Pydantic models) instead of complex class hierarchies.

```python
# ✅ GOOD: Simple, inspectable data
from pydantic import BaseModel

class Message(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str | list[ContentBlock]
    tool_call_id: str | None = None

# ❌ BAD: Complex inheritance, hidden state
class Message:
    def __init__(self):
        self._internal_state = {}
        self._processors = []
```

### 2. Explicit Over Implicit

**Principle**: All behavior should be explicit and visible to the user.

```python
# ✅ GOOD: Explicit parameters
response = await chat(
    model=model,
    messages=messages,
    temperature=0.7,
    max_tokens=1000
)

# ❌ BAD: Hidden configuration
response = await model.chat(messages)  # Where do temperature/tokens come from?
```

### 3. Functions Over Frameworks

**Principle**: Use standard Python features for composition, not custom DSLs.

```python
# ✅ GOOD: Standard async/await
async def pipeline(text: str) -> str:
    messages = [{"role": "user", "content": text}]
    response = await chat(model, messages)
    return extract_content(response)

# ❌ BAD: Custom DSL
pipeline = Chain()
    .add_step("format")
    .add_step("chat")
    .add_step("extract")
    .build()
```

### 4. Provider Agnostic

**Principle**: Same code works with any provider via protocol/ABC.

```python
# ✅ GOOD: Works with any provider
async def process(model: ChatModel, text: str) -> str:
    response = await model.chat([user_message(text)])
    return response.content

# Works with:
await process(OpenAIModel(...), text)
await process(AnthropicModel(...), text)
await process(GroqModel(...), text)
```

### 5. Async-First

**Principle**: All I/O operations must be async, with optional sync wrappers.

```python
# ✅ GOOD: Async by default
async def chat(model: ChatModel, messages: list[Message]) -> Response:
    return await model.chat(messages)

# Optional sync wrapper
def chat_sync(model: ChatModel, messages: list[Message]) -> Response:
    return asyncio.run(chat(model, messages))

# ❌ BAD: Sync only
def chat(model: ChatModel, messages: list[Message]) -> Response:
    return requests.post(...)  # Blocking!
```

---

## Technology Stack

### Required Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.11"  # Minimum Python 3.11 for modern type hints
pydantic = "^2.0"  # Data validation and serialization
httpx = "^0.27"    # Async HTTP client
numpy = "^1.26"    # Vector operations for RAG
structlog = "^24.0"  # Structured logging

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
pytest-cov = "^4.1"
mypy = "^1.8"
ruff = "^0.1"  # Linting and formatting
black = "^24.0"
```

### Optional Dependencies

```toml
[tool.poetry.extras]
rag = ["chromadb", "sentence-transformers"]
vector-stores = ["faiss-cpu", "qdrant-client", "pinecone-client"]
all = ["chromadb", "sentence-transformers", "faiss-cpu"]
```

---

## Project Structure

```
conduit-py/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── .python-version
│
├── src/
│   └── conduit/
│       ├── __init__.py              # Public API exports
│       ├── py.typed                 # PEP 561 marker
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── protocols.py         # ABC definitions (ChatModel, Embeddable)
│       │   ├── models.py            # Pydantic models (Message, Response, etc.)
│       │   ├── chat.py              # Main chat functions
│       │   └── capabilities.py      # Model capability queries
│       │
│       ├── schema/
│       │   ├── __init__.py
│       │   ├── messages.py          # Message schemas
│       │   ├── responses.py         # Response schemas
│       │   ├── tools.py             # Tool schemas
│       │   └── options.py           # ChatOptions, etc.
│       │
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base.py              # Base provider class
│       │   ├── openai.py            # OpenAI implementation
│       │   ├── anthropic.py         # Anthropic implementation
│       │   ├── groq.py              # Groq implementation
│       │   ├── grok.py              # xAI Grok implementation
│       │   └── mock.py              # Testing mock provider
│       │
│       ├── interceptors/
│       │   ├── __init__.py
│       │   ├── base.py              # Interceptor protocol
│       │   ├── context.py           # Context management
│       │   ├── execution.py         # Interceptor chain execution
│       │   ├── retry.py             # Retry interceptor
│       │   ├── logging.py           # Logging interceptor
│       │   ├── cache.py             # Cache interceptor
│       │   ├── cost_tracking.py     # Cost tracking interceptor
│       │   ├── rate_limit.py        # Rate limiting interceptor
│       │   └── timeout.py           # Timeout interceptor
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── definition.py        # Tool definition
│       │   ├── execution.py         # Tool execution
│       │   └── schema_conversion.py # Pydantic -> JSON Schema
│       │
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── loop.py              # Tool loop implementation
│       │   ├── agent.py             # Agent creation
│       │   └── callbacks.py         # Agent callbacks
│       │
│       ├── rag/
│       │   ├── __init__.py
│       │   ├── chain.py             # RAG chain
│       │   ├── retriever.py         # Retriever protocol
│       │   ├── splitters.py         # Text splitters
│       │   ├── embeddings.py        # Embedding models
│       │   └── stores/
│       │       ├── __init__.py
│       │       ├── base.py          # VectorStore protocol
│       │       ├── memory.py        # In-memory store
│       │       ├── chroma.py        # ChromaDB integration
│       │       └── faiss.py         # FAISS integration
│       │
│       ├── memory/
│       │   ├── __init__.py
│       │   ├── base.py              # Memory protocol
│       │   ├── conversation.py      # Conversation memory
│       │   ├── windowed.py          # Windowed memory
│       │   └── summarizing.py       # Summarizing memory
│       │
│       ├── flow/
│       │   ├── __init__.py
│       │   ├── pipeline.py          # Pipeline composition
│       │   └── graph.py             # Graph workflows
│       │
│       ├── streaming/
│       │   ├── __init__.py
│       │   ├── events.py            # Stream event types
│       │   ├── collectors.py        # Stream -> Response collectors
│       │   └── utils.py             # Stream utilities
│       │
│       ├── structured/
│       │   ├── __init__.py
│       │   ├── output.py            # Structured output
│       │   └── extraction.py        # Data extraction
│       │
│       ├── errors/
│       │   ├── __init__.py
│       │   ├── base.py              # Base exceptions
│       │   └── handlers.py          # Error handling utilities
│       │
│       └── utils/
│           ├── __init__.py
│           ├── http.py              # HTTP utilities
│           ├── json.py              # JSON utilities
│           └── tokens.py            # Token estimation
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/
│   │   ├── test_core.py
│   │   ├── test_interceptors.py
│   │   ├── test_tools.py
│   │   └── ...
│   ├── integration/
│   │   ├── test_providers.py
│   │   ├── test_agent.py
│   │   └── ...
│   └── e2e/
│       └── test_workflows.py
│
├── examples/
│   ├── basic_chat.py
│   ├── streaming.py
│   ├── tool_calling.py
│   ├── agent_loop.py
│   ├── rag_pipeline.py
│   └── interceptors.py
│
└── docs/
    ├── index.md
    ├── quickstart.md
    ├── architecture.md
    ├── providers.md
    ├── tools.md
    ├── agents.md
    ├── rag.md
    ├── interceptors.md
    └── api/
        └── ... (auto-generated)
```

---

## Implementation Guidelines by Module

### Module 1: Core Protocols (`core/protocols.py`)

**Purpose**: Define the abstract interfaces that all providers must implement.

```python
"""Core protocols for Conduit.

This module defines the abstract base classes that all providers must implement.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator
from conduit.schema.messages import Message
from conduit.schema.responses import Response, StreamEvent
from conduit.schema.options import ChatOptions
from conduit.core.models import ModelInfo, EmbeddingResult


class ChatModel(ABC):
    """Abstract base class for chat models.
    
    All LLM providers must implement this interface to be compatible with Conduit.
    """
    
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        options: ChatOptions | None = None
    ) -> Response:
        """Send messages to the model and receive a response.
        
        Args:
            messages: List of message objects to send to the model
            options: Optional chat options (temperature, max_tokens, etc.)
            
        Returns:
            Response object containing the model's reply
            
        Raises:
            ProviderError: If the provider API returns an error
            ValidationError: If messages or options are invalid
            TimeoutError: If the request times out
        """
        ...
    
    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        options: ChatOptions | None = None
    ) -> AsyncIterator[StreamEvent]:
        """Stream response from the model.
        
        Args:
            messages: List of message objects to send to the model
            options: Optional chat options
            
        Yields:
            StreamEvent objects as they arrive from the provider
            
        Raises:
            ProviderError: If the provider API returns an error
            ValidationError: If messages or options are invalid
        """
        ...
    
    @abstractmethod
    def model_info(self) -> ModelInfo:
        """Get information about this model.
        
        Returns:
            ModelInfo object with provider, model name, and capabilities
        """
        ...


class Embeddable(ABC):
    """Abstract base class for embedding models."""
    
    @abstractmethod
    async def embed(
        self,
        texts: str | list[str],
        options: dict | None = None
    ) -> EmbeddingResult:
        """Generate embeddings for text(s).
        
        Args:
            texts: Single text string or list of text strings
            options: Optional provider-specific options
            
        Returns:
            EmbeddingResult with embeddings and usage information
        """
        ...
```

**Implementation Requirements**:
1. ✅ Use `ABC` and `@abstractmethod` for all protocols
2. ✅ All I/O methods must be `async`
3. ✅ Include comprehensive docstrings with Args, Returns, Raises
4. ✅ Use type hints for all parameters and return values
5. ✅ Import all types from `conduit.schema.*` modules

---

### Module 2: Schema Models (`schema/`)

**Purpose**: Define all data structures using Pydantic for validation.

```python
"""Message schemas for Conduit."""

from typing import Literal, Union
from pydantic import BaseModel, Field, field_validator


class TextBlock(BaseModel):
    """Text content block."""
    type: Literal["text"] = "text"
    text: str = Field(..., min_length=1)


class ImageSource(BaseModel):
    """Image source (URL or base64)."""
    type: Literal["url", "base64"]
    url: str | None = None
    data: str | None = None
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"] | None = None
    
    @field_validator("url", "data")
    @classmethod
    def validate_source(cls, v, info):
        """Ensure either url or data is provided based on type."""
        if info.data.get("type") == "url" and not info.data.get("url"):
            raise ValueError("url is required when type is 'url'")
        if info.data.get("type") == "base64" and not info.data.get("data"):
            raise ValueError("data is required when type is 'base64'")
        return v


class ImageBlock(BaseModel):
    """Image content block."""
    type: Literal["image"] = "image"
    source: ImageSource


ContentBlock = Union[str, TextBlock, ImageBlock]


class Message(BaseModel):
    """Chat message.
    
    Examples:
        >>> Message(role="user", content="Hello!")
        >>> Message(role="assistant", content="Hi there!")
        >>> Message(
        ...     role="user",
        ...     content=[
        ...         TextBlock(text="What's in this image?"),
        ...         ImageBlock(source=ImageSource(type="url", url="..."))
        ...     ]
        ... )
    """
    role: Literal["user", "assistant", "system", "tool"]
    content: str | list[ContentBlock]
    name: str | None = None
    tool_call_id: str | None = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        }
    }


class ToolCall(BaseModel):
    """Tool invocation requested by the model."""
    id: str
    type: Literal["function"] = "function"
    function: "FunctionCall"


class FunctionCall(BaseModel):
    """Function call details."""
    name: str
    arguments: dict  # Parsed JSON arguments


class Usage(BaseModel):
    """Token usage information."""
    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    total_tokens: int | None = Field(None, ge=0)
    cache_read_tokens: int | None = Field(None, ge=0)
    cache_creation_tokens: int | None = Field(None, ge=0)


class Response(BaseModel):
    """Unified response format from all providers."""
    id: str | None = None
    role: Literal["assistant"] = "assistant"
    content: str | list[ContentBlock]
    model: str | None = None
    stop_reason: Literal["end_turn", "tool_use", "max_tokens", "stop_sequence", "content_filter"] | None = None
    usage: Usage
    tool_calls: list[ToolCall] | None = None
    
    def extract_content(self) -> str:
        """Extract text content from response.
        
        Returns:
            String content, extracting from TextBlocks if content is a list
        """
        if isinstance(self.content, str):
            return self.content
        
        # Extract text from content blocks
        texts = []
        for block in self.content:
            if isinstance(block, str):
                texts.append(block)
            elif isinstance(block, TextBlock):
                texts.append(block.text)
        return "".join(texts)
```

**Implementation Requirements**:
1. ✅ All schemas must inherit from `pydantic.BaseModel`
2. ✅ Use `Field()` for constraints and metadata
3. ✅ Use `Literal` for enums
4. ✅ Use `Union` or `|` for sum types
5. ✅ Include `model_config` with examples
6. ✅ Add helper methods (e.g., `extract_content()`)
7. ✅ Use `@field_validator` for complex validation
8. ✅ Include comprehensive docstrings with examples

---

### Module 3: Providers (`providers/`)

**Purpose**: Implement ChatModel protocol for each LLM provider.

```python
"""OpenAI provider implementation."""

import httpx
from typing import AsyncIterator
from conduit.core.protocols import ChatModel, Embeddable
from conduit.schema.messages import Message
from conduit.schema.responses import Response, StreamEvent
from conduit.schema.options import ChatOptions
from conduit.core.models import ModelInfo, Capabilities
from conduit.errors import ProviderError, RateLimitError, AuthenticationError
from conduit.utils.http import create_client


class OpenAIModel(ChatModel, Embeddable):
    """OpenAI ChatGPT model implementation.
    
    Examples:
        >>> model = OpenAIModel(api_key="sk-...", model="gpt-4")
        >>> response = await model.chat([Message(role="user", content="Hello")])
        >>> print(response.content)
    """
    
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gpt-4",
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 60.0,
        max_retries: int = 2
    ):
        """Initialize OpenAI model.
        
        Args:
            api_key: OpenAI API key
            model: Model identifier (e.g., "gpt-4", "gpt-3.5-turbo")
            base_url: API base URL (for custom endpoints)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = create_client(
            timeout=self.timeout,
            max_retries=self.max_retries
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = create_client(
                timeout=self.timeout,
                max_retries=self.max_retries
            )
        return self._client
    
    async def chat(
        self,
        messages: list[Message],
        options: ChatOptions | None = None
    ) -> Response:
        """Send chat request to OpenAI.
        
        Args:
            messages: List of messages
            options: Optional chat options
            
        Returns:
            Response from the model
            
        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            ProviderError: For other API errors
        """
        opts = options or ChatOptions()
        
        # Build request payload
        payload = {
            "model": self.model,
            "messages": [self._transform_message(msg) for msg in messages],
        }
        
        # Add optional parameters
        if opts.temperature is not None:
            payload["temperature"] = opts.temperature
        if opts.max_tokens is not None:
            payload["max_tokens"] = opts.max_tokens
        if opts.tools:
            payload["tools"] = [self._transform_tool(t) for t in opts.tools]
        
        # Make request
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        
        # Parse response
        data = response.json()
        return self._parse_response(data)
    
    async def stream(
        self,
        messages: list[Message],
        options: ChatOptions | None = None
    ) -> AsyncIterator[StreamEvent]:
        """Stream chat response from OpenAI.
        
        Args:
            messages: List of messages
            options: Optional chat options
            
        Yields:
            StreamEvent objects as they arrive
        """
        opts = options or ChatOptions()
        
        payload = {
            "model": self.model,
            "messages": [self._transform_message(msg) for msg in messages],
            "stream": True,
        }
        
        if opts.temperature is not None:
            payload["temperature"] = opts.temperature
        if opts.max_tokens is not None:
            payload["max_tokens"] = opts.max_tokens
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        
                        event = self._parse_stream_event(data)
                        if event:
                            yield event
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
    
    def model_info(self) -> ModelInfo:
        """Get model information."""
        return ModelInfo(
            provider="openai",
            model=self.model,
            capabilities=Capabilities(
                streaming=True,
                tool_calling=True,
                vision="gpt-4-vision" in self.model,
                json_mode=True,
                max_context=self._get_context_window()
            )
        )
    
    async def embed(
        self,
        texts: str | list[str],
        options: dict | None = None
    ) -> EmbeddingResult:
        """Generate embeddings using OpenAI."""
        # Implementation...
        pass
    
    def _transform_message(self, msg: Message) -> dict:
        """Transform Conduit message to OpenAI format."""
        result = {"role": msg.role, "content": msg.content}
        if msg.name:
            result["name"] = msg.name
        if msg.tool_call_id:
            result["tool_call_id"] = msg.tool_call_id
        return result
    
    def _transform_tool(self, tool) -> dict:
        """Transform Conduit tool to OpenAI format."""
        # Implementation...
        pass
    
    def _parse_response(self, data: dict) -> Response:
        """Parse OpenAI response to Conduit format."""
        choice = data["choices"][0]
        message = choice["message"]
        
        return Response(
            id=data.get("id"),
            content=message.get("content", ""),
            model=data.get("model"),
            stop_reason=self._parse_stop_reason(choice.get("finish_reason")),
            usage=Usage(
                input_tokens=data["usage"]["prompt_tokens"],
                output_tokens=data["usage"]["completion_tokens"],
                total_tokens=data["usage"]["total_tokens"]
            ),
            tool_calls=self._parse_tool_calls(message.get("tool_calls"))
        )
    
    def _parse_stream_event(self, data: str) -> StreamEvent | None:
        """Parse SSE event to StreamEvent."""
        # Implementation...
        pass
    
    def _handle_http_error(self, error: httpx.HTTPStatusError) -> None:
        """Handle HTTP errors and raise appropriate exceptions."""
        status = error.response.status_code
        
        if status == 401:
            raise AuthenticationError("Invalid API key")
        elif status == 429:
            raise RateLimitError("Rate limit exceeded")
        else:
            raise ProviderError(f"OpenAI API error: {error}")
    
    def _get_context_window(self) -> int:
        """Get context window size for model."""
        windows = {
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 16385,
        }
        return windows.get(self.model, 8192)
```

**Implementation Requirements**:
1. ✅ Implement both `ChatModel` and `Embeddable` (if supported)
2. ✅ Use async context manager (`__aenter__`, `__aexit__`)
3. ✅ Create HTTP client lazily or in context manager
4. ✅ Transform between Conduit format and provider format
5. ✅ Handle all HTTP errors appropriately
6. ✅ Parse streaming responses correctly
7. ✅ Include provider-specific capabilities
8. ✅ Add comprehensive error handling
9. ✅ Use type hints everywhere

---

### Module 4: Interceptors (`interceptors/`)

**Purpose**: Implement middleware pattern for cross-cutting concerns.

```python
"""Interceptor base classes and execution."""

from typing import Protocol, Callable, Any
from dataclasses import dataclass, field
from conduit.schema.messages import Message
from conduit.schema.responses import Response
from conduit.schema.options import ChatOptions
from conduit.core.protocols import ChatModel


@dataclass
class Context:
    """Execution context for interceptor chain.
    
    Attributes:
        model: The ChatModel instance
        messages: Original messages
        opts: Original options
        response: Response (set after model call)
        transformed_messages: Modified messages (optional)
        transformed_opts: Modified options (optional)
        metadata: Arbitrary metadata shared between interceptors
        terminated: Whether to terminate early
        error: Any error that occurred
    """
    model: ChatModel
    messages: list[Message]
    opts: ChatOptions
    response: Response | None = None
    transformed_messages: list[Message] | None = None
    transformed_opts: ChatOptions | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    terminated: bool = False
    error: Exception | None = None
    
    def get_messages(self) -> list[Message]:
        """Get messages to use (transformed or original)."""
        return self.transformed_messages or self.messages
    
    def get_opts(self) -> ChatOptions:
        """Get options to use (transformed or original)."""
        return self.transformed_opts or self.opts


class Interceptor(Protocol):
    """Protocol for interceptors.
    
    Interceptors can implement any combination of enter, leave, and error methods.
    """
    
    async def enter(self, ctx: Context) -> Context:
        """Called before the model call.
        
        Args:
            ctx: Current context
            
        Returns:
            Modified context
        """
        return ctx
    
    async def leave(self, ctx: Context) -> Context:
        """Called after successful model call.
        
        Args:
            ctx: Current context with response
            
        Returns:
            Modified context
        """
        return ctx
    
    async def error(self, ctx: Context, error: Exception) -> Context:
        """Called when an error occurs.
        
        Args:
            ctx: Current context
            error: The exception that occurred
            
        Returns:
            Modified context (can clear error to continue)
        """
        ctx.error = error
        return ctx


async def execute_interceptors(
    model: ChatModel,
    messages: list[Message],
    interceptors: list[Interceptor],
    opts: ChatOptions | None = None
) -> Response:
    """Execute chat with interceptor chain.
    
    Args:
        model: ChatModel instance
        messages: Messages to send
        interceptors: List of interceptors
        opts: Optional chat options
        
    Returns:
        Response from model
        
    Raises:
        Exception: If error occurs and is not handled by interceptors
    """
    ctx = Context(
        model=model,
        messages=messages,
        opts=opts or ChatOptions()
    )
    
    # Enter phase (forward through interceptors)
    for interceptor in interceptors:
        if ctx.terminated:
            break
        try:
            ctx = await interceptor.enter(ctx)
        except Exception as e:
            ctx.error = e
            break
    
    # Model call (if not terminated and no error)
    if not ctx.terminated and not ctx.error:
        try:
            ctx.response = await model.chat(
                ctx.get_messages(),
                ctx.get_opts()
            )
        except Exception as e:
            ctx.error = e
    
    # Error phase (if error occurred)
    if ctx.error:
        for interceptor in reversed(interceptors):
            try:
                ctx = await interceptor.error(ctx, ctx.error)
                if not ctx.error:  # Error was cleared
                    break
            except Exception as e:
                ctx.error = e
    
    # Leave phase (backward through interceptors)
    for interceptor in reversed(interceptors):
        try:
            ctx = await interceptor.leave(ctx)
        except Exception as e:
            ctx.error = e
    
    # Raise if error remains
    if ctx.error:
        raise ctx.error
    
    return ctx.response
```

**Example Interceptor Implementation**:

```python
"""Retry interceptor."""

import asyncio
from dataclasses import dataclass
from conduit.interceptors.base import Interceptor, Context
from conduit.errors import RateLimitError, ServerError


@dataclass
class RetryInterceptor:
    """Retry failed requests with exponential backoff.
    
    Examples:
        >>> interceptor = RetryInterceptor(max_attempts=3)
        >>> response = await execute_interceptors(
        ...     model, messages, [interceptor]
        ... )
    """
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: float = 0.1
    
    async def enter(self, ctx: Context) -> Context:
        """Initialize retry metadata."""
        ctx.metadata["retry_attempt"] = 0
        return ctx
    
    async def error(self, ctx: Context, error: Exception) -> Context:
        """Handle errors with retry logic."""
        attempt = ctx.metadata.get("retry_attempt", 0)
        
        # Check if error is retryable
        if not self._is_retryable(error):
            return ctx
        
        # Check if we have attempts left
        if attempt >= self.max_attempts - 1:
            return ctx
        
        # Calculate delay with exponential backoff and jitter
        delay = min(
            self.initial_delay * (self.multiplier ** attempt),
            self.max_delay
        )
        jitter_amount = delay * self.jitter
        delay += (asyncio.get_event_loop().time() % jitter_amount)
        
        # Wait before retry
        await asyncio.sleep(delay)
        
        # Increment attempt counter
        ctx.metadata["retry_attempt"] = attempt + 1
        
        # Clear error to trigger retry
        ctx.error = None
        
        # Retry the model call
        try:
            ctx.response = await ctx.model.chat(
                ctx.get_messages(),
                ctx.get_opts()
            )
        except Exception as e:
            ctx.error = e
        
        return ctx
    
    def _is_retryable(self, error: Exception) -> bool:
        """Check if error is retryable."""
        return isinstance(error, (RateLimitError, ServerError, TimeoutError))
```

**Implementation Requirements**:
1. ✅ Use `@dataclass` for interceptor configuration
2. ✅ Implement `Interceptor` protocol
3. ✅ Use `Context` for state passing
4. ✅ Handle errors gracefully
5. ✅ Use `ctx.metadata` for inter-interceptor communication
6. ✅ Support early termination via `ctx.terminated`
7. ✅ Clear `ctx.error` to continue after handling

---

### Module 5: Tools (`tools/`)

**Purpose**: Define and execute function calling tools.

```python
"""Tool definition and execution."""

from typing import Callable, Any, Type
from pydantic import BaseModel, Field
from conduit.schema.tools import ToolCall


class Tool(BaseModel):
    """Tool definition for function calling.
    
    Examples:
        >>> class WeatherParams(BaseModel):
        ...     location: str
        ...     unit: Literal["celsius", "fahrenheit"] = "celsius"
        >>> 
        >>> def get_weather(params: WeatherParams) -> dict:
        ...     return {"temp": 72, "condition": "sunny"}
        >>> 
        >>> tool = Tool(
        ...     name="get_weather",
        ...     description="Get current weather for a location",
        ...     parameters=WeatherParams,
        ...     fn=get_weather
        ... )
    """
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    description: str = Field(..., min_length=1)
    parameters: Type[BaseModel]
    fn: Callable[[BaseModel], Any]
    
    model_config = {"arbitrary_types_allowed": True}
    
    def execute(self, arguments: dict) -> Any:
        """Execute tool with arguments.
        
        Args:
            arguments: Raw arguments dict
            
        Returns:
            Tool execution result
            
        Raises:
            ValidationError: If arguments don't match schema
        """
        # Validate and parse arguments
        params = self.parameters(**arguments)
        
        # Execute function
        return self.fn(params)
    
    def to_json_schema(self) -> dict:
        """Convert to OpenAI tool format.
        
        Returns:
            Dict in OpenAI tool calling format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters.model_json_schema()
            }
        }


async def execute_tool_calls(
    tools: list[Tool],
    tool_calls: list[ToolCall]
) -> list[dict]:
    """Execute multiple tool calls.
    
    Args:
        tools: Available tools
        tool_calls: Tool calls from model
        
    Returns:
        List of tool result messages
    """
    results = []
    
    for call in tool_calls:
        # Find tool by name
        tool = next((t for t in tools if t.name == call.function.name), None)
        if not tool:
            results.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": f"Error: Tool '{call.function.name}' not found"
            })
            continue
        
        # Execute tool
        try:
            result = tool.execute(call.function.arguments)
            content = result if isinstance(result, str) else str(result)
        except Exception as e:
            content = f"Error executing tool: {str(e)}"
        
        results.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": content
        })
    
    return results
```

**Implementation Requirements**:
1. ✅ Use Pydantic models for parameter schemas
2. ✅ Validate arguments before execution
3. ✅ Convert to JSON Schema for API calls
4. ✅ Handle execution errors gracefully
5. ✅ Return structured results

---

### Module 6: Agent (`agent/`)

**Purpose**: Implement autonomous agent loops with tool execution.

```python
"""Agent tool loop implementation."""

from dataclasses import dataclass
from typing import Callable
from conduit.core.protocols import ChatModel
from conduit.schema.messages import Message
from conduit.schema.responses import Response
from conduit.schema.options import ChatOptions
from conduit.tools.definition import Tool
from conduit.tools.execution import execute_tool_calls
from conduit.errors import MaxIterationsError


@dataclass
class AgentResult:
    """Result from agent execution."""
    response: Response
    messages: list[Message]
    iterations: int
    tool_calls_made: list[dict]


async def tool_loop(
    model: ChatModel,
    messages: list[Message],
    *,
    tools: list[Tool],
    max_iterations: int = 10,
    on_tool_call: Callable[[dict], None] | None = None,
    on_response: Callable[[Response, int], None] | None = None,
    chat_opts: ChatOptions | None = None
) -> AgentResult:
    """Run agent tool loop until completion.
    
    Args:
        model: ChatModel instance
        messages: Initial messages
        tools: Available tools
        max_iterations: Maximum loop iterations
        on_tool_call: Optional callback for each tool call
        on_response: Optional callback for each response
        chat_opts: Optional chat options
        
    Returns:
        AgentResult with final response and history
        
    Raises:
        MaxIterationsError: If max iterations reached without completion
        
    Examples:
        >>> result = await tool_loop(
        ...     model=model,
        ...     messages=[Message(role="user", content="What's the weather?")],
        ...     tools=[weather_tool],
        ...     max_iterations=5
        ... )
        >>> print(result.response.content)
    """
    opts = chat_opts or ChatOptions()
    opts.tools = tools
    
    current_messages = list(messages)
    all_tool_calls = []
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Call model
        response = await model.chat(current_messages, opts)
        
        # Callback
        if on_response:
            on_response(response, iteration)
        
        # Check if done
        if not response.tool_calls:
            return AgentResult(
                response=response,
                messages=current_messages + [response],
                iterations=iteration,
                tool_calls_made=all_tool_calls
            )
        
        # Execute tools
        for tool_call in response.tool_calls:
            if on_tool_call:
                on_tool_call(tool_call)
            all_tool_calls.append(tool_call)
        
        # Add assistant message with tool calls
        current_messages.append(Message(
            role="assistant",
            content=response.content or "",
            tool_calls=response.tool_calls
        ))
        
        # Execute tools and add results
        tool_results = await execute_tool_calls(tools, response.tool_calls)
        for result in tool_results:
            current_messages.append(Message(**result))
    
    raise MaxIterationsError(
        f"Agent exceeded maximum iterations ({max_iterations})"
    )


def make_agent(
    model: ChatModel,
    tools: list[Tool],
    *,
    system_message: str | None = None,
    max_iterations: int = 10,
    chat_opts: ChatOptions | None = None
) -> Callable[[str], AgentResult]:
    """Create a simple agent function.
    
    Args:
        model: ChatModel instance
        tools: Available tools
        system_message: Optional system message
        max_iterations: Maximum loop iterations
        chat_opts: Optional chat options
        
    Returns:
        Async function that takes user message and returns AgentResult
        
    Examples:
        >>> agent = make_agent(
        ...     model=model,
        ...     tools=[weather_tool, search_tool],
        ...     system_message="You are a helpful assistant."
        ... )
        >>> result = await agent("What's the weather in Tokyo?")
    """
    async def agent_fn(user_message: str) -> AgentResult:
        messages = []
        if system_message:
            messages.append(Message(role="system", content=system_message))
        messages.append(Message(role="user", content=user_message))
        
        return await tool_loop(
            model=model,
            messages=messages,
            tools=tools,
            max_iterations=max_iterations,
            chat_opts=chat_opts
        )
    
    return agent_fn
```

**Implementation Requirements**:
1. ✅ Implement iterative tool loop
2. ✅ Handle tool execution errors
3. ✅ Support callbacks for observability
4. ✅ Maintain message history
5. ✅ Enforce max iterations
6. ✅ Return comprehensive results

---

### Module 7: RAG (`rag/`)

**Purpose**: Implement retrieval-augmented generation pipeline.

```python
"""RAG chain implementation."""

from typing import Callable
from conduit.core.protocols import ChatModel
from conduit.schema.messages import Message
from conduit.rag.retriever import Retriever, RetrievalResult


DEFAULT_TEMPLATE = """Use the following context to answer the question. If you cannot answer based on the context, say so.

Context:
{context}

Question: {question}

Answer:"""


class RAGChain:
    """RAG chain for question answering.
    
    Examples:
        >>> chain = RAGChain(
        ...     model=model,
        ...     retriever=retriever,
        ...     k=5
        ... )
        >>> result = await chain("What is machine learning?")
        >>> print(result["answer"])
    """
    
    def __init__(
        self,
        *,
        model: ChatModel,
        retriever: Retriever,
        template: str = DEFAULT_TEMPLATE,
        k: int = 5,
        format_context: Callable[[list[RetrievalResult]], str] | None = None
    ):
        """Initialize RAG chain.
        
        Args:
            model: ChatModel instance
            retriever: Retriever instance
            template: Prompt template with {context} and {question}
            k: Number of documents to retrieve
            format_context: Optional function to format context
        """
        self.model = model
        self.retriever = retriever
        self.template = template
        self.k = k
        self.format_context = format_context or self._default_format_context
    
    async def __call__(self, question: str) -> dict:
        """Execute RAG chain.
        
        Args:
            question: User question
            
        Returns:
            Dict with answer, sources, usage, and scores
        """
        # Retrieve relevant documents
        results = await self.retriever.retrieve(question, k=self.k)
        
        # Format context
        context = self.format_context(results)
        
        # Build prompt
        prompt = self.template.format(context=context, question=question)
        
        # Call model
        response = await self.model.chat([
            Message(role="user", content=prompt)
        ])
        
        return {
            "answer": response.extract_content(),
            "sources": [r.document for r in results],
            "usage": response.usage,
            "scores": [r.score for r in results]
        }
    
    def _default_format_context(self, results: list[RetrievalResult]) -> str:
        """Default context formatting."""
        return "\n\n---\n\n".join(
            r.document.content for r in results
        )
```

**Implementation Requirements**:
1. ✅ Implement retriever protocol
2. ✅ Support custom prompt templates
3. ✅ Format context appropriately
4. ✅ Return sources and scores
5. ✅ Support custom context formatting

---

## Code Style & Standards

### General Rules

1. **Python Version**: Minimum Python 3.11
2. **Formatting**: Use `black` with default settings
3. **Linting**: Use `ruff` with strict settings
4. **Type Checking**: Use `mypy` in strict mode
5. **Docstrings**: Google style docstrings for all public APIs
6. **Imports**: Use `isort` with black-compatible settings

### Type Hints

```python
# ✅ GOOD: Comprehensive type hints
async def chat(
    model: ChatModel,
    messages: list[Message],
    *,
    options: ChatOptions | None = None
) -> Response:
    ...

# ❌ BAD: Missing type hints
async def chat(model, messages, options=None):
    ...
```

### Error Handling

```python
# ✅ GOOD: Specific exceptions with context
from conduit.errors import ProviderError, ValidationError

try:
    response = await model.chat(messages)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        raise AuthenticationError("Invalid API key") from e
    raise ProviderError(f"API error: {e}") from e

# ❌ BAD: Bare except, no context
try:
    response = await model.chat(messages)
except:
    raise Exception("Error")
```

### Async Patterns

```python
# ✅ GOOD: Proper async context manager
async with OpenAIModel(api_key="...") as model:
    response = await model.chat(messages)

# ✅ GOOD: Async generator for streaming
async def stream(self, messages: list[Message]) -> AsyncIterator[StreamEvent]:
    async for line in response.aiter_lines():
        yield parse_event(line)

# ❌ BAD: Blocking I/O in async function
async def chat(self, messages):
    return requests.post(url, json=data)  # Blocking!
```

### Configuration

```python
# pyproject.toml

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP", "ANN", "B", "A", "C4", "DTZ", "T10", "EM", "ISC", "ICN", "G", "PIE", "T20", "PT", "Q", "RET", "SIM", "TID", "TCH", "ARG", "PTH", "PD", "PGH", "PL", "TRY", "NPY", "RUF"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

---

## Testing Requirements

### Test Structure

```python
"""Tests for OpenAI provider."""

import pytest
from conduit.providers.openai import OpenAIModel
from conduit.schema.messages import Message
from conduit.errors import AuthenticationError


class TestOpenAIModel:
    """Test suite for OpenAI provider."""
    
    @pytest.fixture
    async def model(self):
        """Create test model."""
        async with OpenAIModel(
            api_key="test-key",
            model="gpt-4"
        ) as model:
            yield model
    
    @pytest.mark.asyncio
    async def test_chat_success(self, model, httpx_mock):
        """Test successful chat request."""
        # Mock API response
        httpx_mock.add_response(
            url="https://api.openai.com/v1/chat/completions",
            json={
                "id": "chatcmpl-123",
                "choices": [{
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15
                }
            }
        )
        
        # Test
        response = await model.chat([
            Message(role="user", content="Hi")
        ])
        
        # Assert
        assert response.content == "Hello!"
        assert response.usage.input_tokens == 10
        assert response.usage.output_tokens == 5
    
    @pytest.mark.asyncio
    async def test_chat_authentication_error(self, model, httpx_mock):
        """Test authentication error handling."""
        httpx_mock.add_response(
            url="https://api.openai.com/v1/chat/completions",
            status_code=401,
            json={"error": {"message": "Invalid API key"}}
        )
        
        with pytest.raises(AuthenticationError):
            await model.chat([Message(role="user", content="Hi")])
    
    @pytest.mark.asyncio
    async def test_stream(self, model, httpx_mock):
        """Test streaming response."""
        # Mock streaming response
        httpx_mock.add_response(
            url="https://api.openai.com/v1/chat/completions",
            content=b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\ndata: [DONE]\n\n'
        )
        
        # Collect stream
        events = []
        async for event in model.stream([Message(role="user", content="Hi")]):
            events.append(event)
        
        # Assert
        assert len(events) > 0
        assert events[0].type == "content_delta"
```

### Coverage Requirements

- **Minimum coverage**: 80%
- **Critical paths**: 100% coverage required
- **Integration tests**: Required for all providers
- **E2E tests**: Required for main workflows

---

## Documentation Standards

### Module Docstrings

```python
"""OpenAI provider implementation.

This module provides the OpenAI implementation of the ChatModel protocol,
supporting GPT-3.5, GPT-4, and other OpenAI models.

Examples:
    Basic usage:
    
    >>> async with OpenAIModel(api_key="sk-...") as model:
    ...     response = await model.chat([
    ...         Message(role="user", content="Hello!")
    ...     ])
    ...     print(response.content)
    
    With streaming:
    
    >>> async for event in model.stream(messages):
    ...     if event.type == "content_delta":
    ...         print(event.text, end="")
"""
```

### Function Docstrings

```python
async def chat(
    model: ChatModel,
    messages: list[Message],
    *,
    options: ChatOptions | None = None
) -> Response:
    """Send messages to a chat model and receive a response.
    
    This is the main entry point for synchronous chat interactions. For
    streaming responses, use the `stream` function instead.
    
    Args:
        model: ChatModel instance (e.g., OpenAIModel, AnthropicModel)
        messages: List of message objects to send to the model
        options: Optional chat options including temperature, max_tokens,
            tools, and other provider-specific parameters
    
    Returns:
        Response object containing the model's reply, usage information,
        and any tool calls
    
    Raises:
        ValidationError: If messages or options are invalid
        AuthenticationError: If API credentials are invalid
        RateLimitError: If rate limit is exceeded
        ProviderError: For other API errors
    
    Examples:
        Basic chat:
        
        >>> response = await chat(
        ...     model,
        ...     [Message(role="user", content="What is 2+2?")]
        ... )
        >>> print(response.content)
        "4"
        
        With options:
        
        >>> response = await chat(
        ...     model,
        ...     messages,
        ...     options=ChatOptions(temperature=0.7, max_tokens=100)
        ... )
        
        With tools:
        
        >>> response = await chat(
        ...     model,
        ...     messages,
        ...     options=ChatOptions(tools=[weather_tool])
        ... )
    
    See Also:
        - stream: For streaming responses
        - chat_with_interceptors: For adding middleware
    """
    ...
```

---

## Migration Mapping Reference

### Clojure → Python Quick Reference

| Clojure | Python | Notes |
|---------|--------|-------|
| `defprotocol` | `class Protocol` or `ABC` | Use ABC for runtime checks |
| `defrecord` | `@dataclass` or `BaseModel` | Use Pydantic for validation |
| `core.async` channels | `AsyncIterator` | Use async generators |
| `go-loop` | `async for` | More Pythonic |
| `<!` | `async for` or `await` | Depends on context |
| `atom` | `asyncio.Lock` + dict | For shared state |
| `comp` | Function composition | Use decorators or manual |
| `->` | Method chaining | `.method1().method2()` |
| `->>` | Pipe operator | Use `|` or manual |
| `map`, `filter` | Comprehensions | `[x for x in ...]` |
| `reduce` | `functools.reduce` | Or comprehension |
| Malli schemas | Pydantic models | Better IDE support |
| Keywords | `Literal` types | For enums |
| Maps | `dict` or `BaseModel` | Prefer Pydantic |
| Vectors | `list` | With type hints |
| Sets | `set` | With type hints |

### Pattern Translations

#### Pattern 1: Protocol Implementation

```clojure
;; Clojure
(defprotocol ChatModel
  (chat [model messages opts]))

(defrecord OpenAIModel [config]
  ChatModel
  (chat [this messages opts]
    ...))
```

```python
# Python
from abc import ABC, abstractmethod

class ChatModel(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        options: ChatOptions | None = None
    ) -> Response:
        ...

class OpenAIModel(ChatModel):
    def __init__(self, config: dict):
        self.config = config
    
    async def chat(
        self,
        messages: list[Message],
        options: ChatOptions | None = None
    ) -> Response:
        ...
```

#### Pattern 2: Streaming

```clojure
;; Clojure
(let [ch (c/stream model messages)]
  (go-loop []
    (when-let [event (<! ch)]
      (print (:text event))
      (recur))))
```

```python
# Python
async for event in model.stream(messages):
    if event.type == "content_delta":
        print(event.text, end="")
```

#### Pattern 3: Interceptors

```clojure
;; Clojure
(c/chat-with-interceptors
  model
  messages
  [(retry-interceptor {:max-attempts 3})
   (logging-interceptor)])
```

```python
# Python
response = await execute_interceptors(
    model,
    messages,
    [
        RetryInterceptor(max_attempts=3),
        LoggingInterceptor()
    ]
)
```

#### Pattern 4: Tool Execution

```clojure
;; Clojure
(def weather-tool
  {:name "get_weather"
   :description "Get weather"
   :schema [:map [:location :string]]
   :fn (fn [{:keys [location]}] ...)})
```

```python
# Python
class WeatherParams(BaseModel):
    location: str

def get_weather(params: WeatherParams) -> dict:
    ...

weather_tool = Tool(
    name="get_weather",
    description="Get weather",
    parameters=WeatherParams,
    fn=get_weather
)
```

---

## Common Patterns & Recipes

### Pattern 1: Provider Implementation Template

```python
"""Template for implementing a new provider."""

import httpx
from typing import AsyncIterator
from conduit.core.protocols import ChatModel
from conduit.schema.messages import Message
from conduit.schema.responses import Response, StreamEvent
from conduit.schema.options import ChatOptions
from conduit.core.models import ModelInfo, Capabilities


class MyProviderModel(ChatModel):
    """My provider implementation."""
    
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://api.provider.com/v1",
        timeout: float = 60.0
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def chat(
        self,
        messages: list[Message],
        options: ChatOptions | None = None
    ) -> Response:
        # 1. Build request
        payload = self._build_request(messages, options)
        
        # 2. Make API call
        response = await self.client.post(
            f"{self.base_url}/chat",
            json=payload,
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        # 3. Parse response
        return self._parse_response(response.json())
    
    async def stream(
        self,
        messages: list[Message],
        options: ChatOptions | None = None
    ) -> AsyncIterator[StreamEvent]:
        payload = self._build_request(messages, options)
        payload["stream"] = True
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/chat",
            json=payload,
            headers=self._get_headers()
        ) as response:
            async for line in response.aiter_lines():
                event = self._parse_stream_line(line)
                if event:
                    yield event
    
    def model_info(self) -> ModelInfo:
        return ModelInfo(
            provider="my_provider",
            model=self.model,
            capabilities=Capabilities(
                streaming=True,
                tool_calling=True,
                vision=False,
                json_mode=True,
                max_context=8192
            )
        )
    
    def _build_request(
        self,
        messages: list[Message],
        options: ChatOptions | None
    ) -> dict:
        """Transform to provider format."""
        ...
    
    def _parse_response(self, data: dict) -> Response:
        """Transform from provider format."""
        ...
    
    def _parse_stream_line(self, line: str) -> StreamEvent | None:
        """Parse SSE line to StreamEvent."""
        ...
    
    def _get_headers(self) -> dict:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
```

### Pattern 2: Custom Interceptor Template

```python
"""Template for custom interceptor."""

from dataclasses import dataclass
from conduit.interceptors.base import Interceptor, Context


@dataclass
class MyInterceptor:
    """My custom interceptor.
    
    Args:
        my_param: Description of parameter
    """
    my_param: str
    
    async def enter(self, ctx: Context) -> Context:
        """Called before model call."""
        # Modify messages
        # ctx.transformed_messages = modify(ctx.messages)
        
        # Modify options
        # ctx.transformed_opts = modify(ctx.opts)
        
        # Add metadata
        # ctx.metadata["my_key"] = "value"
        
        return ctx
    
    async def leave(self, ctx: Context) -> Context:
        """Called after successful model call."""
        # Modify response
        # ctx.response = modify(ctx.response)
        
        # Log or track
        # logger.info("Response received", tokens=ctx.response.usage.total_tokens)
        
        return ctx
    
    async def error(self, ctx: Context, error: Exception) -> Context:
        """Called on error."""
        # Handle specific errors
        # if isinstance(error, MyError):
        #     ctx.error = None  # Clear to continue
        
        return ctx
```

### Pattern 3: Custom Tool Template

```python
"""Template for custom tool."""

from pydantic import BaseModel, Field
from conduit.tools.definition import Tool


class MyToolParams(BaseModel):
    """Parameters for my tool."""
    param1: str = Field(..., description="Description of param1")
    param2: int = Field(default=10, ge=1, le=100, description="Description of param2")


def my_tool_function(params: MyToolParams) -> dict:
    """Execute my tool logic.
    
    Args:
        params: Validated parameters
        
    Returns:
        Tool result as dict
    """
    # Your logic here
    result = do_something(params.param1, params.param2)
    
    return {
        "result": result,
        "status": "success"
    }


# Create tool
my_tool = Tool(
    name="my_tool",
    description="Clear description of what this tool does",
    parameters=MyToolParams,
    fn=my_tool_function
)
```

---

## Implementation Checklist

### Phase 1: Core Foundation
- [ ] Set up project structure
- [ ] Configure pyproject.toml with dependencies
- [ ] Implement core protocols (ChatModel, Embeddable)
- [ ] Implement schema models (Message, Response, etc.)
- [ ] Implement error classes
- [ ] Set up testing infrastructure
- [ ] Write unit tests for core

### Phase 2: Providers
- [ ] Implement base provider class
- [ ] Implement OpenAI provider
- [ ] Implement Anthropic provider
- [ ] Implement Groq provider
- [ ] Implement mock provider for testing
- [ ] Write integration tests for each provider

### Phase 3: Interceptors
- [ ] Implement interceptor base and context
- [ ] Implement execution engine
- [ ] Implement retry interceptor
- [ ] Implement logging interceptor
- [ ] Implement cache interceptor
- [ ] Implement cost tracking interceptor
- [ ] Implement rate limit interceptor
- [ ] Write tests for all interceptors

### Phase 4: Tools & Agents
- [ ] Implement tool definition and execution
- [ ] Implement schema conversion
- [ ] Implement agent tool loop
- [ ] Implement agent creation helpers
- [ ] Write tests for tools and agents

### Phase 5: RAG
- [ ] Implement text splitters
- [ ] Implement embedding models
- [ ] Implement vector store protocol
- [ ] Implement in-memory vector store
- [ ] Implement retriever
- [ ] Implement RAG chain
- [ ] Write tests for RAG components

### Phase 6: Advanced Features
- [ ] Implement memory management
- [ ] Implement workflow pipelines
- [ ] Implement structured output
- [ ] Implement streaming utilities
- [ ] Write tests for advanced features

### Phase 7: Documentation & Polish
- [ ] Write comprehensive README
- [ ] Write API documentation
- [ ] Write usage guides
- [ ] Create examples
- [ ] Set up CI/CD
- [ ] Publish to PyPI

---

## Final Notes for AI Agents

### Critical Success Factors

1. **Type Safety First**: Every function must have complete type hints
2. **Async Everywhere**: All I/O must be async with optional sync wrappers
3. **Pydantic for Data**: Use Pydantic models for all data structures
4. **Test Coverage**: Maintain >80% coverage, 100% for critical paths
5. **Documentation**: Every public API needs comprehensive docstrings
6. **Error Handling**: Use specific exceptions with helpful messages
7. **Python Idioms**: Follow Python conventions, not Clojure patterns

### Common Pitfalls to Avoid

1. ❌ Don't use blocking I/O in async functions
2. ❌ Don't use plain dicts where Pydantic models should be used
3. ❌ Don't skip type hints "for now"
4. ❌ Don't copy Clojure patterns literally
5. ❌ Don't forget to close HTTP clients
6. ❌ Don't use bare `except:` clauses
7. ❌ Don't skip docstrings for "simple" functions

### When in Doubt

1. Prefer Pydantic over plain dicts
2. Prefer async generators over channels
3. Prefer explicit over implicit
4. Prefer composition over inheritance
5. Prefer type safety over flexibility
6. Prefer standard library over dependencies
7. Prefer clarity over cleverness

---

**End of Guide**

This document should be followed strictly when implementing Conduit in Python. Any deviations should be documented and justified.
