# Running Alembic Migrations in Docker

## Automatic Migrations

**Good news!** Migrations run **automatically** when the `apex` container starts. The Dockerfile is configured to run:

```bash
alembic upgrade head && poetry run uvicorn apex.api.main:app
```

So when you do `docker-compose up`, migrations run before the server starts.

## Creating a New Migration

Since we just added new models (KnowledgeBase, Document, Tool, Agent, AgentTool), you need to **create a migration** first.

### Option 1: Create Migration Inside Container (Recommended)

```bash
# 1. Make sure containers are running
docker-compose up -d

# 2. Create the migration inside the apex container
docker-compose exec apex alembic revision --autogenerate -m "Add knowledge bases, tools, and agents"

# 3. The migration file will be created in apex/migrations/versions/
# 4. Restart the container to apply it (or it will auto-apply on next restart)
docker-compose restart apex
```

### Option 2: Create Migration Locally (If you have Python/Poetry set up)

```bash
cd apex
poetry run alembic revision --autogenerate -m "Add knowledge bases, tools, and agents"
```

Then restart the container:
```bash
docker-compose restart apex
```

## Manual Migration Commands

If you need to run migrations manually inside the container:

```bash
# Run all pending migrations
docker-compose exec apex alembic upgrade head

# Rollback one migration
docker-compose exec apex alembic downgrade -1

# Check current migration status
docker-compose exec apex alembic current

# Show migration history
docker-compose exec apex alembic history
```

## First Time Setup (After Adding New Models)

1. **Create the migration**:
   ```bash
   docker-compose exec apex alembic revision --autogenerate -m "Add knowledge bases, tools, and agents"
   ```

2. **Review the generated migration file**:
   ```bash
   # Check the latest file in apex/migrations/versions/
   ls -lt apex/migrations/versions/ | head -1
   ```

3. **Apply the migration** (happens automatically on restart, or manually):
   ```bash
   docker-compose restart apex
   # OR
   docker-compose exec apex alembic upgrade head
   ```

## Troubleshooting

### Migration Fails on Startup

If migrations fail when the container starts, check logs:
```bash
docker-compose logs apex
```

Common issues:
- Database not ready yet → Wait for postgres health check
- Migration conflicts → Check migration history
- Import errors → Ensure all models are imported in `migrations/env.py`

### Database Connection Issues

If migrations can't connect to the database:
```bash
# Check if postgres is running
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Verify DATABASE_URL in container
docker-compose exec apex env | grep DATABASE_URL
```

### Reset Everything

If you need to start fresh:
```bash
# Stop and remove everything including volumes
docker-compose down -v

# Rebuild
docker-compose build

# Start (migrations will run automatically)
docker-compose up -d
```

## Current Setup

Your Dockerfile (line 59) already runs migrations automatically:
```dockerfile
CMD ["sh", "-c", "alembic upgrade head && poetry run uvicorn apex.api.main:app --host 0.0.0.0 --port 8000"]
```

So you only need to:
1. **Create** the migration once (for new models)
2. **Restart** the container (migration applies automatically)
