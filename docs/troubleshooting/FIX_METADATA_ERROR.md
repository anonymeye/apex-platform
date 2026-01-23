# Fixing the Metadata Error

## The Problem
SQLAlchemy reserves `metadata` as a special attribute name. Even though we renamed the Python attribute to `meta_data`, Python might be using cached bytecode.

## Solution Steps

### Option 1: Rebuild Container (Recommended)

```bash
# Stop containers
docker-compose down

# Rebuild the apex container (forces fresh Python cache)
docker-compose build --no-cache apex

# Start containers
docker-compose up -d
```

### Option 2: Clear Python Cache in Running Container

```bash
# Clear cache
docker-compose exec apex find /workspace/apex/src -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
docker-compose exec apex find /workspace/apex/src -name "*.pyc" -delete 2>/dev/null || true

# Restart
docker-compose restart apex
```

### Option 3: Force Python to Recompile

```bash
# Restart with PYTHONDONTWRITEBYTECODE=1
docker-compose exec apex sh -c "PYTHONDONTWRITEBYTECODE=1 python -c 'from apex.models.knowledge import KnowledgeBase; print(\"OK\")'"
```

## Verify the Fix

After rebuilding/restarting, check logs:

```bash
docker-compose logs apex --tail=50
```

You should see the server starting successfully, not the metadata error.

## If Still Failing

If you still see the error after rebuilding, verify the file is correct:

```bash
# Check the actual file in container
docker-compose exec apex cat /workspace/apex/src/apex/models/knowledge.py | grep -A 2 "meta_data"
```

You should see:
```python
meta_data: Mapped[Optional[dict]] = mapped_column("meta_data", JSON, nullable=True, default=dict)
```

NOT:
```python
metadata: Mapped[Optional[dict]] = ...
```
