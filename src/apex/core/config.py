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
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
