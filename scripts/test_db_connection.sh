#!/bin/bash
# Test database connection from apex container

set -e

echo "=== Testing Database Connection ==="
echo ""

# Get container info
echo "Checking if apex container is running..."
if ! docker ps | grep -q apex_backend; then
    echo "ERROR: apex_backend container is not running!"
    echo "Start it with: docker-compose up -d apex"
    exit 1
fi

echo "✓ apex_backend container is running"
echo ""

# Check environment variables
echo "Checking DATABASE_URL environment variable..."
docker exec apex_backend sh -c 'echo $DATABASE_URL' | sed 's/:[^:@]*@/:****@/'
echo ""

# Test PostgreSQL connection from apex container
echo "Testing PostgreSQL connection from apex container..."
if docker exec apex_backend sh -c 'pg_isready -h postgres -U postgres' > /dev/null 2>&1; then
    echo "✓ PostgreSQL is reachable via pg_isready"
else
    echo "✗ PostgreSQL is NOT reachable via pg_isready"
fi
echo ""

# Test with psql
echo "Testing actual database connection with psql..."
if docker exec apex_backend sh -c 'PGPASSWORD=postgres psql -h postgres -U postgres -d apex_db -c "SELECT 1" > /dev/null 2>&1' 2>/dev/null; then
    echo "✓ Database connection successful with psql"
else
    echo "✗ Database connection failed with psql"
    echo "Trying to get more details..."
    docker exec apex_backend sh -c 'PGPASSWORD=postgres psql -h postgres -U postgres -d apex_db -c "SELECT 1"' || true
fi
echo ""

# Test Python asyncpg connection
echo "Testing Python asyncpg connection..."
docker exec apex_backend sh -c 'python3 -c "
import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect(
            host=\"postgres\",
            port=5432,
            user=\"postgres\",
            password=\"postgres\",
            database=\"apex_db\"
        )
        await conn.close()
        print(\"✓ asyncpg connection successful\")
        return True
    except Exception as e:
        print(f\"✗ asyncpg connection failed: {e}\")
        return False

asyncio.run(test())
"'

echo ""
echo "=== Test Complete ==="
