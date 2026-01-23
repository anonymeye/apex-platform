# Troubleshooting Container Startup Failures

## Quick Debug Steps

### 1. Check Container Logs

```bash
# View recent logs
docker-compose logs apex --tail=100

# Follow logs in real-time
docker-compose logs -f apex
```

### 2. Check if Container is Running

```bash
docker-compose ps
```

If the container shows "Restarting" or "Exited", check the logs.

### 3. Common Issues and Fixes

#### Issue: Import Errors During Migration

**Symptoms**: Container keeps restarting, logs show ImportError

**Fix**: 
1. Check that all models are imported in `migrations/env.py`
2. Verify all imports in model files are correct
3. Rebuild the container:
   ```bash
   docker-compose build apex
   docker-compose up -d apex
   ```

#### Issue: Database Connection Failed

**Symptoms**: Connection timeout or "could not connect" errors

**Fix**:
1. Ensure postgres container is running: `docker-compose ps postgres`
2. Check DATABASE_URL in environment
3. Wait for postgres to be healthy before apex starts

#### Issue: Alembic Migration Fails

**Symptoms**: Migration errors in logs

**Fix**: 
1. Temporarily disable auto-migration (see below)
2. Run migration manually to see full error
3. Fix the issue
4. Re-enable auto-migration

## Temporarily Disable Auto-Migration

To debug startup issues, you can temporarily disable automatic migrations:

### Option 1: Modify Dockerfile CMD (Temporary)

Edit `apex/Dockerfile` line 59:
```dockerfile
# Original (runs migrations):
CMD ["sh", "-c", "alembic upgrade head && poetry run uvicorn apex.api.main:app --host 0.0.0.0 --port 8000"]

# Temporary (skip migrations):
CMD ["poetry", "run", "uvicorn", "apex.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Then rebuild:
```bash
docker-compose build apex
docker-compose up -d apex
```

### Option 2: Override CMD in docker-compose.yml

Add to `apex` service in `docker-compose.yml`:
```yaml
apex:
  # ... existing config ...
  command: poetry run uvicorn apex.api.main:app --host 0.0.0.0 --port 8000
```

Then restart:
```bash
docker-compose up -d apex
```

## Run Migrations Manually (After Fixing Issues)

Once the container starts successfully:

```bash
# Create migration
docker-compose exec apex alembic revision --autogenerate -m "Add knowledge bases, tools, and agents"

# Apply migration
docker-compose exec apex alembic upgrade head
```

## Check Specific Errors

### Python Import Errors

```bash
# Test imports inside container
docker-compose exec apex python -c "from apex.models.base import Base; print('OK')"
```

### Database Connection

```bash
# Test database connection
docker-compose exec apex python -c "from apex.core.config import settings; print(settings.database_url)"
```

### Check Alembic Config

```bash
# Check alembic can see models
docker-compose exec apex alembic current
```

## Full Reset (Nuclear Option)

If nothing works, reset everything:

```bash
# Stop and remove everything including volumes
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```
