"""Alembic environment configuration."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import your models' Base and all models so Alembic can detect them
from apex.models.base import Base
# Import all models so Alembic can detect them for autogenerate
from apex.models.user import Organization, OrganizationMember, User  # noqa: F401
from apex.models.knowledge import Document, KnowledgeBase  # noqa: F401
from apex.models.tool import AgentTool, Tool  # noqa: F401
from apex.models.agent import Agent  # noqa: F401
from apex.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the SQLAlchemy URL from settings
# Convert async URL to sync URL for Alembic (use psycopg2 for migrations)
sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
config.set_main_option("sqlalchemy.url", sync_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    Includes retry logic with exponential backoff to handle
    transient database connection issues.
    """
    import time
    from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError
    
    # Import psycopg2 exceptions if available (for sync migrations)
    try:
        import psycopg2
        from psycopg2 import OperationalError as Psycopg2OperationalError
        from psycopg2 import errors as psycopg2_errors
        # Combine exception types that might be raised
        connection_exceptions = (
            SQLAlchemyOperationalError,
            Psycopg2OperationalError,
            psycopg2_errors.OperationalError,
        )
    except ImportError:
        # psycopg2 not available, only catch SQLAlchemy exceptions
        connection_exceptions = (SQLAlchemyOperationalError,)
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Retry connection with exponential backoff
    max_retries = 5
    retry_delay = 2
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            with connectable.connect() as connection:
                context.configure(connection=connection, target_metadata=target_metadata)

                with context.begin_transaction():
                    context.run_migrations()
            # Success - break out of retry loop
            if attempt > 0:
                print(f"Migration succeeded on attempt {attempt + 1}", flush=True)
            break
        except connection_exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                error_msg = str(e).split('\n')[0]  # Get first line of error
                print(
                    f"Database connection failed (attempt {attempt + 1}/{max_retries}): {error_msg}",
                    flush=True
                )
                print(f"Retrying in {wait_time} seconds...", flush=True)
                time.sleep(wait_time)
            else:
                # Final attempt failed
                print(f"Failed to connect to database after {max_retries} attempts.", flush=True)
                print(f"Last error: {str(last_exception)}", flush=True)
                raise
        except Exception as e:
            # Non-connection errors should not be retried
            print(f"Migration failed with non-retryable error: {str(e)}", flush=True)
            raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
