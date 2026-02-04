# Conduit Examples

This directory contains example implementations demonstrating how to use Conduit's features.

## Examples

### Basic Examples

- **`basic_chat.py`** - Simple chat completion
- **`streaming.py`** - Streaming responses token by token
- **`tool_calling.py`** - Function calling with tools
- **`agent_loop.py`** - Autonomous agent with tool execution

### Advanced Examples

- **`with_interceptors.py`** - Using middleware (retry, cache, logging)
- **`rag_pipeline.py`** - Retrieval-Augmented Generation pipeline
- **`structured_output.py`** - Extracting structured data from responses
- **`memory_management.py`** - Conversation memory strategies
- **`multi_provider.py`** - Using multiple LLM providers

### Complete Applications

- **`policy_support_agent.py`** - Customer support agent with RAG

## Running Examples

Most examples can run with mock models for demonstration, but for full functionality, you'll need API keys:

```bash
export OPENAI_API_KEY="sk-..."      # For OpenAI models
export ANTHROPIC_API_KEY="sk-..."  # For Anthropic models
export GROQ_API_KEY="gsk_..."      # For Groq models
```

Run any example:

```bash
python examples/basic_chat.py
python examples/streaming.py
python examples/agent_loop.py
```

## Example Descriptions

### Basic Chat
Simple synchronous chat completion with a model.

### Streaming
Stream responses as they're generated for real-time output.

### Tool Calling
Define functions that the model can call during conversation.

### Agent Loop
Autonomous agents that can use multiple tools to complete tasks.

### With Interceptors
Middleware for retry logic, caching, logging, and more.

### RAG Pipeline
Retrieval-Augmented Generation for document-based Q&A.

### Structured Output
Extract Pydantic models, JSON, and structured data from responses.

### Memory Management
Manage conversation history with different strategies.

### Multi Provider
Switch between OpenAI, Anthropic, and Groq seamlessly.
