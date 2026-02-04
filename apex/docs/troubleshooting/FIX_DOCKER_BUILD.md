# Fixing Docker Build Cache Error

## The Error
```
failed to solve: failed to prepare extraction snapshot ... parent snapshot does not exist: not found
```

This is a Docker build cache corruption issue.

## Solutions (Try in Order)

### Solution 1: Prune Docker Build Cache

```bash
# Remove all build cache
docker builder prune -af

# Then rebuild
docker-compose build --no-cache apex
docker-compose up -d apex
```

### Solution 2: Remove Specific Image and Rebuild

```bash
# Remove the apex image
docker rmi chat_assistant-apex:latest 2>/dev/null || true
docker rmi $(docker images | grep apex | awk '{print $3}') 2>/dev/null || true

# Rebuild without cache
docker-compose build --no-cache apex
docker-compose up -d apex
```

### Solution 3: Full Docker Cleanup (Nuclear Option)

```bash
# Stop all containers
docker-compose down

# Remove all build cache and unused images
docker system prune -af --volumes

# Rebuild everything
docker-compose build --no-cache
docker-compose up -d
```

### Solution 4: Use BuildKit (If Available)

```bash
# Enable BuildKit and rebuild
DOCKER_BUILDKIT=1 docker-compose build --no-cache apex
docker-compose up -d apex
```

## Quick Fix (Recommended)

Run these commands in order:

```bash
# 1. Stop containers
docker-compose down

# 2. Clean build cache
docker builder prune -af

# 3. Remove problematic image
docker rmi chat_assistant-apex 2>/dev/null || true

# 4. Rebuild
docker-compose build --no-cache apex

# 5. Start
docker-compose up -d apex

# 6. Check logs
docker-compose logs -f apex
```

## If Still Failing

If the build still fails, try rebuilding the entire project:

```bash
docker-compose down -v
docker system prune -af
docker-compose build --no-cache
docker-compose up -d
```
