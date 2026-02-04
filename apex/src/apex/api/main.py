"""FastAPI application entry point."""

import json
import logging
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, DisconnectionError, DatabaseError

# Load environment variables from .env file
# dotenv searches current directory and parent directories automatically
load_dotenv(override=True)

# Debug: Log if GROQ_API_KEY is loaded (for troubleshooting)
if os.getenv("GROQ_API_KEY"):
    print("✓ GROQ_API_KEY loaded from environment", flush=True)
else:
    print("⚠ GROQ_API_KEY not found in environment", flush=True)

from apex.api.v1.routes import agents, auth, chat, connections, knowledge, model_refs, tools
from apex.core.config import settings
from apex.core.database import close_db
from apex.utils.logging import setup_logging
from redis.asyncio import Redis

# Configure logging so DEBUG/INFO etc. are visible (e.g. LOG_LEVEL=DEBUG in Docker)
setup_logging(debug=settings.debug, log_level=settings.log_level)

# Get loggers
logger = logging.getLogger("uvicorn.error")
access_logger = logging.getLogger("uvicorn.access")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    print("=" * 80, flush=True)
    print("APEX API STARTING UP", flush=True)
    print("=" * 80, flush=True)
    logger.info("=" * 80)
    logger.info("APEX API STARTING UP")
    logger.info("=" * 80)
    
    # Preload embedding model
    print("Preloading embedding model...", flush=True)
    logger.info(f"Preloading embedding model: {settings.embedding_model}")
    try:
        from apex.ml.rag.embeddings import EmbeddingService
        from apex.storage.vector_store import create_vector_store
        
        # Preload embedding service
        embedding_service = EmbeddingService(
            model_name=settings.embedding_model,
            batch_size=settings.embedding_batch_size,
        )
        # Warm up the model with a dummy embedding to ensure it's loaded
        await embedding_service.embed("warmup")
        
        # Preload vector store (pgvector or memory per config)
        vector_store = create_vector_store()
        
        # Store in app state for access by routes
        app.state.embedding_service = embedding_service
        app.state.vector_store = vector_store

        print(f"✓ Embedding model '{settings.embedding_model}' loaded successfully", flush=True)
        logger.info(f"Embedding model '{settings.embedding_model}' preloaded successfully")
    except Exception as e:
        print(f"⚠ Failed to preload embedding model: {e}", flush=True)
        logger.error(f"Failed to preload embedding model: {e}", exc_info=True)
        # Don't fail startup - allow lazy loading as fallback
        app.state.embedding_service = None
        app.state.vector_store = None

    # Redis for conversation state
    try:
        redis_client = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        app.state.redis = redis_client
        print("✓ Redis connected for conversation state", flush=True)
        logger.info("Redis connected for conversation state")
    except Exception as e:
        print(f"⚠ Redis connection failed: {e}", flush=True)
        logger.error("Redis connection failed: %s", e, exc_info=True)
        app.state.redis = None

    # Database schema is managed by Alembic migrations (run in Dockerfile before startup)
    yield
    # Shutdown
    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.aclose()
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with error handling."""
    try:
        response = await call_next(request)
        if response.status_code == 422:
            access_logger.error(
                f'{request.client.host if request.client else "unknown"} - '
                f'"{request.method} {request.url.path} HTTP/1.1" {response.status_code} VALIDATION_ERROR'
            )
        return response
    except Exception as e:
        # Log the exception before re-raising so it can be handled by exception handlers
        logger.error(
            f"Unhandled exception in middleware for {request.method} {request.url.path}: {str(e)}",
            exc_info=True,
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            }
        )
        raise

# Exception handler for database connection errors
@app.exception_handler(OperationalError)
async def database_operational_error_handler(request: Request, exc: OperationalError):
    """Handle database operational errors (connection failures, etc.)."""
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    logger.error(
        f"Database operational error: {error_msg}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path,
            "error_type": type(exc).__name__,
            "error_message": error_msg,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database connection error. Please check database availability.",
            "error": "database_unavailable",
        },
    )


@app.exception_handler(DisconnectionError)
async def database_disconnection_error_handler(request: Request, exc: DisconnectionError):
    """Handle database disconnection errors."""
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    logger.error(
        f"Database disconnection error: {error_msg}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path,
            "error_type": type(exc).__name__,
            "error_message": error_msg,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database connection lost. Please retry.",
            "error": "database_disconnected",
        },
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle general database errors."""
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    logger.error(
        f"Database error: {error_msg}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path,
            "error_type": type(exc).__name__,
            "error_message": error_msg,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error occurred.",
            "error": "database_error",
        },
    )


# Exception handler for validation errors
# FastAPI automatically calls this handler when RequestValidationError is raised
# during request body validation (before your endpoint function is called)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors for debugging.
    
    This handler is automatically invoked by FastAPI when:
    - Request body doesn't match the expected Pydantic model
    - Required fields are missing
    - Field validation fails (e.g., min_length, max_length, type mismatches)
    """
    try:
        body = await request.body()
        body_str = body.decode('utf-8') if body else 'Empty body'
    except Exception as e:
        body_str = f"Error reading body: {e}"
    
    # Format errors for readability
    errors_str = json.dumps(exc.errors(), indent=2)
    
    # Log using uvicorn access logger format (matches existing log format)
    access_logger.error(f'VALIDATION_ERROR: {request.method} {request.url.path}')
    access_logger.error(f'Errors: {errors_str}')
    access_logger.error(f'Body: {body_str}')
    
    # Also print directly (guaranteed to show)
    print(f'\n{"="*80}\nVALIDATION ERROR: {request.method} {request.url.path}\nErrors: {errors_str}\nBody: {body_str}\n{"="*80}\n', flush=True)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": body_str if body_str != 'Empty body' else None
        },
    )


# Global exception handler for all unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with detailed logging."""
    error_type = type(exc).__name__
    error_msg = str(exc)
    
    logger.error(
        f"Unhandled exception: {error_type}: {error_msg}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown",
            "error_type": error_type,
            "error_message": error_msg,
        }
    )
    
    # Print to stdout for immediate visibility
    print(
        f'\n{"="*80}\n'
        f'UNHANDLED EXCEPTION: {error_type}\n'
        f'Path: {request.method} {request.url.path}\n'
        f'Error: {error_msg}\n'
        f'{"="*80}\n',
        flush=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "error": "internal_server_error",
            "error_type": error_type,
        },
    )

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")  # Router already has /agents prefix
app.include_router(connections.router, prefix="/api/v1")
app.include_router(model_refs.router, prefix="/api/v1")
app.include_router(tools.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1/agents")  # Chat routes are under /agents


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Apex API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
