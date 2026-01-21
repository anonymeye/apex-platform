# Database Setup Guide

This document describes the database setup and configuration for the Apex backend.

## Database: PostgreSQL

We're using **PostgreSQL** as the primary database with:
- **Async Driver**: `asyncpg` for async SQLAlchemy operations
- **Sync Driver**: `psycopg2-binary` for Alembic migrations
- **ORM**: SQLAlchemy 2.0+ with async support

## Configuration

### Environment Variables

Create a `.env` file in the `apex/` directory with the following variables:

```env
# Database Configuration
# For async operations, use postgresql+asyncpg://
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/apex_db

# JWT Configuration
SECRET_KEY=your-secret-key-change-in-production-use-a-strong-random-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
APP_NAME=Apex API
DEBUG=False
```

### Database Connection

The database connection is configured in `src/apex/core/config.py` and managed in `src/apex/core/database.py`.

- **Async Engine**: Created using `create_async_engine` with the connection string from settings
- **Session Factory**: `AsyncSessionLocal` creates async database sessions
- **Session Dependency**: `get_db()` provides database sessions to FastAPI route handlers

## Database Models

The following models are defined:

1. **User** (`apex.models.user.User`)
   - Email, name, password hash
   - Active status, super admin flag
   - Organization memberships

2. **Organization** (`apex.models.user.Organization`)
   - Name, slug, subscription tier
   - Description

3. **OrganizationMember** (`apex.models.user.OrganizationMember`)
   - Links users to organizations
   - Role and permissions
   - Active status

All models inherit from `BaseModel` which provides:
- UUID primary keys
- `created_at` and `updated_at` timestamps

## Migrations (Alembic)

### Setup

Alembic is configured for database migrations:

- **Config File**: `alembic.ini`
- **Migration Scripts**: `migrations/env.py`
- **Migration Versions**: `migrations/versions/`

### Creating Migrations

```bash
# Create a new migration (autogenerate from models)
alembic revision --autogenerate -m "Description of changes"

# Or use the helper script
bash scripts/create_initial_migration.sh
```

### Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current migration status
alembic current

# Show migration history
alembic history
```

### Initial Migration

To create the initial migration for User, Organization, and OrganizationMember models:

```bash
cd apex
alembic revision --autogenerate -m "Initial migration: users, organizations, and memberships"
```

Review the generated migration file in `migrations/versions/` before applying it.

## Database Initialization

The database is automatically initialized when the FastAPI application starts via the `lifespan` context manager in `src/apex/api/main.py`. This calls `init_db()` which creates all tables using `Base.metadata.create_all()`.

**Note**: For production, use Alembic migrations instead of `init_db()`.

## Usage in Routes

Database sessions are injected into route handlers using FastAPI's dependency injection:

```python
from apex.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/example")
async def example_route(db: AsyncSession = Depends(get_db)):
    # Use db session here
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

The `get_db()` dependency:
- Creates a new session for each request
- Commits changes on successful completion
- Rolls back on exceptions
- Closes the session when done

## Setup Steps

1. **Install Dependencies**
   ```bash
   cd apex
   poetry install
   ```

2. **Create Database**
   ```bash
   # Using PostgreSQL CLI
   createdb apex_db
   
   # Or using psql
   psql -U postgres -c "CREATE DATABASE apex_db;"
   ```

3. **Configure Environment**
   ```bash
   # Create .env file (see Environment Variables above)
   cp .env.example .env  # If .env.example exists
   # Edit .env with your database credentials
   ```

4. **Run Migrations**
   ```bash
   # Create initial migration
   alembic revision --autogenerate -m "Initial migration"
   
   # Apply migrations
   alembic upgrade head
   ```

5. **Start the Application**
   ```bash
   poetry run uvicorn apex.api.main:app --reload
   ```

## Troubleshooting

### Connection Errors

- Verify PostgreSQL is running: `pg_isready`
- Check database credentials in `.env`
- Ensure the database exists: `psql -l | grep apex_db`

### Migration Issues

- Ensure all models are imported in `migrations/env.py`
- Check that `target_metadata = Base.metadata` includes all models
- Verify the database URL in settings matches your PostgreSQL instance

### Async/Sync Driver Mismatch

- Application uses `asyncpg` (async) - connection string: `postgresql+asyncpg://...`
- Migrations use `psycopg2` (sync) - automatically converted from async URL
- Both drivers should be installed: `asyncpg` and `psycopg2-binary`

## Next Steps

- [ ] Create initial migration
- [ ] Set up database seeding script
- [ ] Add database connection pooling configuration
- [ ] Set up database backups
- [ ] Configure read replicas (if needed)
