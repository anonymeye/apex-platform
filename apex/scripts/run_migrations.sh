#!/bin/bash
# Migration runner script for manual migrations
# Usage: ./scripts/run_migrations.sh [upgrade|downgrade|current|history]

set -e

# Default action
ACTION=${1:-upgrade}

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Apex Database Migrations ===${NC}"
echo ""

# Check if running in Docker or locally
if [ -f /.dockerenv ] || [ -n "${DOCKER_CONTAINER}" ]; then
    echo "Running migrations inside Docker container..."
    POETRY_CMD="poetry run"
else
    echo "Running migrations locally..."
    POETRY_CMD="poetry run"
fi

case "$ACTION" in
    upgrade)
        echo -e "${YELLOW}Upgrading database to latest migration...${NC}"
        $POETRY_CMD alembic upgrade head
        echo -e "${GREEN}✓ Migrations applied successfully${NC}"
        ;;
    downgrade)
        echo -e "${YELLOW}Downgrading database by one migration...${NC}"
        $POETRY_CMD alembic downgrade -1
        echo -e "${GREEN}✓ Migration rolled back${NC}"
        ;;
    current)
        echo -e "${YELLOW}Current migration status:${NC}"
        $POETRY_CMD alembic current
        ;;
    history)
        echo -e "${YELLOW}Migration history:${NC}"
        $POETRY_CMD alembic history
        ;;
    *)
        echo -e "${RED}Unknown action: $ACTION${NC}"
        echo "Usage: $0 [upgrade|downgrade|current|history]"
        exit 1
        ;;
esac
