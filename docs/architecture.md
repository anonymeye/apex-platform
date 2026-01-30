# Architecture Overview

## Core Principles

Conduit follows a data-first, functional design:

- **Protocols over Classes**: Uses Python ABCs (`ChatModel`, `Embeddable`) for provider abstraction
- **Pydantic Models**: All data structures are Pydantic models for validation and serialization
- **Async-First**: All I/O operations are async
- **Composable**: Components can be combined using standard Python patterns

## Component Layers

### 1. Core Protocols

Defines the interface that all providers implement:

- `ChatModel`: Chat completion interface
- `Embeddable`: Embedding generation interface
- `ModelInfo`: Provider metadata

### 2. Providers

Provider implementations that conform to the protocols:

- `OpenAIModel`: OpenAI API
- `AnthropicModel`: Anthropic API
- `GroqModel`: Groq API
- `MockModel`: Testing provider

### 3. Schema

Pydantic models for messages, responses, and options:

- `Message`: User, assistant, system, tool messages
- `Response`: Model response with content, usage, tool calls
- `ChatOptions`: Temperature, max tokens, etc.

### 4. Interceptors

Middleware system for cross-cutting concerns:

- `RetryInterceptor`: Automatic retries
- `CacheInterceptor`: Response caching
- `LoggingInterceptor`: Request/response logging
- `RateLimitInterceptor`: Rate limiting
- `TimeoutInterceptor`: Request timeouts
- `CostTrackingInterceptor`: Cost tracking

### 5. Tools & Agents

Function calling and autonomous agents:

- `Tool`: Function definition with Pydantic schemas
- `tool_loop`: Agent execution loop
- `make_agent`: Convenience function for creating agents

### 6. RAG Pipeline

Retrieval-augmented generation components:

- `TextSplitter`: Document splitting strategies
- `EmbeddingModel`: Embedding generation wrapper
- `VectorStore`: Vector storage interface
- `Retriever`: Retrieval interface
- `RAGChain`: End-to-end RAG pipeline

### 7. Memory Management

Conversation history management:

- `ConversationMemory`: Store all messages
- `WindowedMemory`: Token-aware sliding window
- `SummarizingMemory`: Compress old messages

### 8. Structured Output

Extract structured data from responses:

- `extract_structured`: Extract Pydantic models
- `extract_json`: Extract JSON
- `classify`: Text classification

## Data Flow

```
User Input → Message → ChatModel → Interceptors → Provider API
                                                      ↓
Response ← Pydantic Model ← JSON Response ← HTTP Response
```

## Interceptor Chain

Interceptors wrap model calls in phases:

1. **Enter**: Before request (modify request, check cache)
2. **Call**: Execute the model call
3. **Leave**: After success (cache response, log)
4. **Error**: On failure (retry, log error)

## Extension Points

- **Custom Providers**: Implement `ChatModel` or `Embeddable`
- **Custom Interceptors**: Implement `Interceptor` protocol
- **Custom Tools**: Define `Tool` with any callable
- **Custom Memory**: Implement `Memory` protocol
- **Custom Vector Stores**: Implement `VectorStore` protocol
