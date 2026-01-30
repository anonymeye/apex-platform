# Installation

## Requirements

- Python 3.11 or higher
- pip or poetry

## Install from PyPI

```bash
pip install conduit-py
```

## Install from Source

```bash
git clone https://github.com/your-org/conduit.git
cd conduit
pip install -e .
```

## Install with Poetry

```bash
poetry add conduit-py
```

## Verify Installation

```python
import conduit
print(conduit.__version__)
```

## Provider-Specific Dependencies

Conduit uses `httpx` for HTTP requests and `pydantic` for data validation. These are installed automatically.

For specific providers, ensure you have the required API keys:
- OpenAI: `OPENAI_API_KEY` environment variable or pass `api_key` parameter
- Anthropic: `ANTHROPIC_API_KEY` environment variable or pass `api_key` parameter
- Groq: `GROQ_API_KEY` environment variable or pass `api_key` parameter
