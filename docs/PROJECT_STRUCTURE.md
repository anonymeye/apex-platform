# Apex - Project Structure

## Overview

This document outlines the proposed project structure for Apex. The structure follows a clean architecture pattern with clear separation of concerns.

## Directory Structure

```
apex/
├── README.md
├── VISION.md
├── PROJECT_STRUCTURE.md
├── pyproject.toml
├── poetry.lock
├── .env.example
├── .gitignore
│
├── src/
│   └── apex/
│       ├── __init__.py
│       │
│       ├── api/                          # FastAPI application
│       │   ├── __init__.py
│       │   ├── main.py                   # FastAPI app entry point
│       │   ├── dependencies.py          # Dependency injection
│       │   ├── middleware.py           # Auth, CORS, logging middleware
│       │   │
│       │   ├── v1/                       # API v1 routes
│       │   │   ├── __init__.py
│       │   │   ├── routes/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── agents.py        # Agent CRUD endpoints
│       │   │   │   ├── chat.py          # Chat endpoints
│       │   │   │   ├── knowledge.py     # Knowledge upload/management
│       │   │   │   ├── schemas.py        # Schema definition endpoints
│       │   │   │   ├── playbooks.py     # Playbook management
│       │   │   │   ├── tools.py         # Tool definition endpoints
│       │   │   │   ├── fine_tuning.py   # Fine-tuning endpoints
│       │   │   │   ├── experiments.py   # Experiment tracking endpoints
│       │   │   │   └── monitoring.py    # Monitoring/metrics endpoints
│       │   │   │
│       │   │   └── schemas/             # Pydantic request/response models
│       │   │       ├── __init__.py
│       │   │       ├── agents.py
│       │   │       ├── chat.py
│       │   │       ├── knowledge.py
│       │   │       ├── schemas.py
│       │   │       ├── playbooks.py
│       │   │       ├── tools.py
│       │   │       ├── fine_tuning.py
│       │   │       └── experiments.py
│       │
│       ├── core/                          # Core business logic
│       │   ├── __init__.py
│       │   ├── config.py                 # Application configuration
│       │   ├── security.py               # Auth, JWT, permissions
│       │   └── exceptions.py            # Custom exceptions
│       │
│       ├── services/                      # Business logic services
│       │   ├── __init__.py
│       │   ├── agent_service.py          # Agent lifecycle management
│       │   ├── chat_service.py           # Chat interaction handling
│       │   ├── knowledge_service.py      # Knowledge ingestion & processing
│       │   ├── schema_service.py         # Schema analysis & management
│       │   ├── playbook_service.py       # Playbook management
│       │   ├── tool_service.py           # Tool registration & execution
│       │   ├── fine_tuning_service.py    # Fine-tuning orchestration
│       │   ├── experiment_service.py     # Experiment tracking
│       │   └── evaluation_service.py     # Response evaluation
│       │
│       ├── models/                        # Database models (SQLAlchemy)
│       │   ├── __init__.py
│       │   ├── base.py                   # Base model class
│       │   ├── user.py                   # User/Tenant models
│       │   ├── agent.py                  # Agent configuration models
│       │   ├── knowledge.py              # Document/knowledge models
│       │   ├── schema.py                 # Schema definition models
│       │   ├── playbook.py               # Playbook models
│       │   ├── tool.py                   # Tool definition models
│       │   ├── fine_tuning.py            # Fine-tuning job models
│       │   ├── experiment.py             # Experiment tracking models
│       │   └── conversation.py           # Chat conversation models
│       │
│       ├── repositories/                  # Data access layer
│       │   ├── __init__.py
│       │   ├── base.py                   # Base repository
│       │   ├── agent_repository.py
│       │   ├── knowledge_repository.py
│       │   ├── schema_repository.py
│       │   ├── playbook_repository.py
│       │   ├── tool_repository.py
│       │   ├── fine_tuning_repository.py
│       │   └── experiment_repository.py
│       │
│       ├── ml/                            # ML/Agent layer
│       │   ├── __init__.py
│       │   │
│       │   ├── agent/                    # Agent orchestration
│       │   │   ├── __init__.py
│       │   │   ├── agent_factory.py      # Create agents from config
│       │   │   ├── agent_executor.py    # Execute agent interactions
│       │   │   └── guardrails.py        # Safety & guardrail checks
│       │   │
│       │   ├── rag/                      # RAG pipeline
│       │   │   ├── __init__.py
│       │   │   ├── pipeline.py          # RAG chain orchestration
│       │   │   ├── retriever.py         # Custom retriever with schema awareness
│       │   │   ├── processor.py         # Document processing (clean, chunk, filter)
│       │   │   └── embeddings.py        # Embedding service wrapper
│       │   │
│       │   ├── fine_tuning/              # Fine-tuning pipeline
│       │   │   ├── __init__.py
│       │   │   ├── dataset_builder.py   # Convert playbooks/Q&A to datasets
│       │   │   ├── trainer.py           # LoRA/QLoRA training orchestration
│       │   │   ├── model_manager.py     # Model versioning & storage
│       │   │   └── evaluator.py         # Model evaluation metrics
│       │   │
│       │   ├── experimentation/          # Experimentation system
│       │   │   ├── __init__.py
│       │   │   ├── experiment_runner.py # Run A/B tests
│       │   │   ├── metrics_collector.py # Collect performance metrics
│       │   │   └── comparator.py        # Compare model variants
│       │   │
│       │   └── tools/                    # Tool execution
│       │       ├── __init__.py
│       │       ├── registry.py          # Tool registry
│       │       ├── executor.py           # Tool execution engine
│       │       └── validators.py         # Tool schema validation
│       │
│       ├── storage/                       # Storage abstractions
│       │   ├── __init__.py
│       │   ├── vector_store.py          # Vector store interface & implementations
│       │   ├── file_storage.py           # File upload/storage (S3/local)
│       │   └── model_storage.py         # Fine-tuned model storage
│       │
│       └── utils/                         # Utilities
│           ├── __init__.py
│           ├── logging.py               # Logging configuration
│           ├── validators.py            # Data validation helpers
│           └── helpers.py               # General helpers
│
├── tests/                                # Test suite
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures
│   │
│   ├── unit/                            # Unit tests
│   │   ├── services/
│   │   ├── ml/
│   │   └── utils/
│   │
│   ├── integration/                     # Integration tests
│   │   ├── api/
│   │   └── ml/
│   │
│   └── e2e/                             # End-to-end tests
│       └── workflows/
│
├── migrations/                           # Database migrations (Alembic)
│   ├── versions/
│   └── env.py
│
├── scripts/                              # Utility scripts
│   ├── setup_db.py
│   ├── seed_data.py
│   └── migrate_models.py
│
├── docs/                                 # Additional documentation
│   ├── api/                             # API documentation
│   ├── deployment/                      # Deployment guides
│   └── development/                     # Development guides
│
└── frontend/                             # Frontend application (future)
    └── (TBD - React/Next.js/Vue)
```

## Key Design Principles

1. **Separation of Concerns**: Clear boundaries between API, services, repositories, and ML layers
2. **Dependency Injection**: Services depend on abstractions (repositories, storage interfaces)
3. **Async-First**: All I/O operations are async to leverage FastAPI's async capabilities
4. **Conduit Integration**: ML layer wraps and extends Conduit components
5. **Multi-tenancy**: All data models include tenant isolation at the repository level

## Module Responsibilities

### `api/`
- FastAPI application setup
- Route handlers (thin layer, delegate to services)
- Request/response validation (Pydantic schemas)
- Authentication/authorization middleware

### `services/`
- Business logic orchestration
- Coordinate between repositories, ML layer, and external services
- Transaction management
- Validation and error handling

### `models/`
- SQLAlchemy ORM models
- Database schema definitions
- Relationships and constraints

### `repositories/`
- Data access abstraction
- Query building
- Multi-tenancy filtering
- Caching (if needed)

### `ml/`
- Conduit integration
- Agent orchestration
- RAG pipeline customization
- Fine-tuning workflows
- Experimentation framework

### `storage/`
- Abstract storage interfaces
- Vector store implementations (Qdrant, etc.)
- File storage (local/S3)
- Model artifact storage

## Integration Points

- **Conduit**: Used in `ml/agent/`, `ml/rag/`, `ml/tools/`
- **Database**: PostgreSQL via SQLAlchemy in `models/` and `repositories/`
- **Vector Store**: Qdrant (or other) via interface in `storage/vector_store.py`
- **Embeddings**: HuggingFace service integration in `ml/rag/embeddings.py`

## Next Steps

1. Review and approve structure
2. Create Technical Architecture Design document with detailed component designs
3. Set up initial project scaffolding
4. Define database schema in detail
5. Design API contracts
