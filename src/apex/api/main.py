"""FastAPI application entry point."""

import json
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apex.api.v1.routes import agents, auth, knowledge
from apex.core.config import settings
from apex.core.database import close_db

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
    # Database schema is managed by Alembic migrations (run in Dockerfile before startup)
    yield
    # Shutdown
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
    """Log all incoming requests."""
    response = await call_next(request)
    if response.status_code == 422:
        access_logger.error(f'{request.client.host if request.client else "unknown"} - "{request.method} {request.url.path} HTTP/1.1" {response.status_code} VALIDATION_ERROR')
    return response

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

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")  # Router already has /agents prefix


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Apex API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
