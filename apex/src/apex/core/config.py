"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Database
    # Default uses 'postgres' service name for Docker, override with DATABASE_URL env var for local dev
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/apex_db"
    
    # Migration control
    # Set to False in production to run migrations manually or via init container
    run_migrations_on_startup: bool = True
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application
    app_name: str = "Apex API"
    debug: bool = False
    # Log level: DEBUG, INFO, WARNING, ERROR (set LOG_LEVEL=DEBUG in Docker to see all logs)
    log_level: str = "INFO"
    
    # Embedding configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_batch_size: int = 32

    # Redis (conversation state: messages + metadata, TTL 1 day)
    redis_url: str = "redis://localhost:6379/0"
    conversation_state_ttl_seconds: int = 86400  # 1 day

    # Evaluation: LLM judge (different model than agent, e.g. GPT-4o-mini)
    judge_model: str = "gpt-4o-mini"
    judge_provider: str = "openai"
    judge_api_key_env_var: str = "OPENAI_API_KEY"

    # Vector store: "pgvector" (persistent, same DB) or "memory" (in-memory, dev only)
    vector_store_type: str = "pgvector"
    # Embedding dimension must match the model (e.g. all-MiniLM-L6-v2 = 384)
    embedding_dimension: int = 384
    # Table name for pgvector store (easy to change if migrating to another schema)
    vector_embeddings_table: str = "vector_embeddings"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
