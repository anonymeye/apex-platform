"""Database connection and session management."""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.exc import OperationalError, DisconnectionError, DatabaseError

from apex.core.config import settings
from apex.models.base import Base

# Get logger for database operations
logger = logging.getLogger("uvicorn.error")

# Log database configuration at startup (sanitized)
db_url_display = settings.database_url.split('@')[-1] if '@' in settings.database_url else "hidden"
logger.info(f"Initializing database connection to: {db_url_display}")
logger.info(f"Database URL driver: {settings.database_url.split(':')[0] if ':' in settings.database_url else 'unknown'}")

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session.
    
    Provides database session with automatic commit/rollback handling.
    Logs database errors for debugging.
    """
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
                logger.debug("Database session committed successfully")
            except (OperationalError, DisconnectionError, DatabaseError) as e:
                await session.rollback()
                error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                logger.error(
                    f"Database error in session: {error_msg}",
                    exc_info=True,
                    extra={
                        "error_type": type(e).__name__,
                        "error_message": error_msg,
                    }
                )
                raise
            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Unexpected error in database session: {str(e)}",
                    exc_info=True,
                    extra={
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    }
                )
                raise
            finally:
                await session.close()
    except (OperationalError, DisconnectionError) as e:
        # Log connection errors at session creation time
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        logger.error(
            f"Failed to create database session: {error_msg}",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "error_message": error_msg,
                "database_url": settings.database_url.split('@')[-1] if '@' in settings.database_url else "hidden",
            }
        )
        raise


async def init_db() -> None:
    """Initialize database (create tables)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
