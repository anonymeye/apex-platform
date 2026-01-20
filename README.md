# Apex

A SaaS platform that enables businesses to build, train, and deploy AI chat agents tailored to their specific knowledge base, processes, and use cases.

## Overview

Apex is an industry-agnostic platform that allows customers to define their own data schemas, tools, and workflows. The platform focuses on showcasing fine-tuning techniques and experimentation capabilities.

## Project Status

**⚠️ This project is not production-ready and is open source for demonstration purposes.**

## Features

- **Agent Builder**: Create and configure AI agents with custom knowledge bases
- **Knowledge Management**: Upload and process documents, policies, and company data
- **Schema-Aware RAG**: Intelligent retrieval with custom schema understanding
- **Fine-tuning Pipeline**: Convert playbooks and Q&A into training datasets for LoRA/QLoRA
- **Experimentation Platform**: A/B test different models and fine-tuning strategies
- **Custom Tools**: Define industry-agnostic tools with flexible schemas
- **Monitoring Dashboard**: Track performance, experiments, and agent interactions

## Architecture

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed project structure.

## Technology Stack

- **Backend**: FastAPI (Python)
- **ML Layer**: Conduit (LLM orchestration library)
- **Database**: PostgreSQL
- **Vector Store**: Qdrant (self-hosted)
- **Embeddings**: HuggingFace (sentence-transformers)
- **Fine-tuning**: PEFT, transformers (LoRA/QLoRA)

## Getting Started

### Prerequisites

- Python 3.11+
- Poetry
- PostgreSQL
- Qdrant (or other vector store)

### Installation

```bash
# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Set up database
python scripts/setup_db.py

# Run migrations
alembic upgrade head
```

### Running the Application

```bash
# Start the API server
poetry run uvicorn apex.api.main:app --reload
```

## Documentation

- [Vision & Design](VISION.md)
- [Project Structure](PROJECT_STRUCTURE.md)

## License

[To be determined]

## Contributing

This is a demonstration project. Contributions welcome for learning and showcasing purposes.
