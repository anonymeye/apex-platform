# Apex Backend Dockerfile
FROM python:3.11-slim

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

# Copy conduit first (needed for Poetry dependency resolution)
# Place it at /conduit so that ../conduit from /app resolves correctly
COPY conduit /conduit

# Set working directory to /app (matches volume mount)
WORKDIR /app

# Copy dependency files first (for better layer caching)
COPY apex/pyproject.toml apex/poetry.lock ./

# Install dependencies
# Conduit is available at /conduit (../conduit from /app)
# At runtime, volume mount will override for development hot-reload
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root && \
    rm -rf /tmp/poetry_cache

# Copy application code (will be overridden by volume mount in development)
COPY apex/src ./src
COPY apex/migrations ./migrations
COPY apex/alembic.ini ./
COPY apex/scripts ./scripts

# Add src to PYTHONPATH so the apex package is importable
# Conduit will be added to PYTHONPATH at runtime via volume mount
ENV PYTHONPATH=/app/src:${PYTHONPATH}

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden in docker-compose.yml for dev mode)
CMD ["sh", "-c", "alembic upgrade head && poetry run uvicorn apex.api.main:app --host 0.0.0.0 --port 8000 --reload"]
