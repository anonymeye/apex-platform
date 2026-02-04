# Conduit

> Simple, functional LLM orchestration for Python

Conduit is a type-safe, async-first library for orchestrating LLM interactions across multiple providers.

## Features

- 🎯 **Simple & Functional**: Data-first design with Pydantic models
- 🔒 **Type-Safe**: 100% type coverage with mypy strict mode
- 🚀 **Async & Sync**: Both async and sync APIs for any use case
- 🔌 **Provider Agnostic**: Same code, any provider (OpenAI, Anthropic, Groq)
- 🛠️ **Tool Calling**: Built-in support for function calling
- 🤖 **Agent Loops**: Autonomous agents with tool execution
- 📚 **RAG Pipeline**: Complete retrieval-augmented generation
- 🔄 **Interceptors**: Middleware for retry, caching, logging, rate limiting

## Installation

```bash
pip install conduit-py
```

## Quick Start

### Async API (Recommended)

```python
from conduit.agent import make_agent
from conduit.providers.openai import OpenAIModel
from conduit.tools import Tool

model = OpenAIModel(api_key="sk-...", model="gpt-4")
agent = make_agent(model, tools=[...])

# Async usage
result = await agent.ainvoke("What's the weather?")
print(result.response.extract_content())
```

### Sync API (For scripts)

```python
from conduit.agent import make_agent
from conduit.providers.openai import OpenAIModel

model = OpenAIModel(api_key="sk-...", model="gpt-4")
agent = make_agent(model, tools=[...])

# Synchronous usage - no await needed!
result = agent.invoke("What's the weather?")
print(result.response.extract_content())
```

## Documentation

- [Installation Guide](docs/installation.md)
- [Quick Start Guide](docs/quickstart.md)
- [Sync & Async API Guide](docs/SYNC_ASYNC_GUIDE.md)
- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api-reference.md)

## License

MIT License - see [LICENSE](LICENSE) file for details.
