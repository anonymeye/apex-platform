# Apex Backend Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==2.2.1

# Configure Poetry: Don't create virtual environment, install dependencies to system
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=0 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Create directory structure to maintain ../conduit path relationship
# We'll work from /workspace to maintain the apex/../conduit structure
WORKDIR /workspace

# Copy conduit first (needed for dependency resolution)
COPY conduit ./conduit

# Copy apex dependency files first
COPY apex/pyproject.toml apex/poetry.lock ./apex/

# Install dependencies first (maintains ../conduit path relationship)
WORKDIR /workspace/apex
RUN poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --only main --no-root && \
    rm -rf /tmp/poetry_cache

# Copy application code
COPY apex/src ./src
COPY apex/migrations ./migrations
COPY apex/alembic.ini ./
COPY apex/scripts ./scripts

# Set working directory to apex for runtime
WORKDIR /workspace/apex

# Add src to PYTHONPATH so the apex package is importable
ENV PYTHONPATH=/workspace/apex/src:${PYTHONPATH}

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && poetry run uvicorn apex.api.main:app --host 0.0.0.0 --port 8000"]
