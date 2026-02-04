#!/bin/bash
# Start fresh containers - stops existing containers and starts clean

set -e

echo "=== Starting Fresh Containers ==="
echo ""

cd "$(dirname "$0")/.."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Step 1: Stopping existing containers...${NC}"
docker-compose down || echo "No containers to stop"

echo ""
echo -e "${YELLOW}Step 2: Removing containers (if any)...${NC}"
docker-compose rm -f || echo "No containers to remove"

echo ""
echo -e "${YELLOW}Step 3: Checking for port conflicts...${NC}"
PORTS=(5432 8000 3000)
CONFLICTS=0

for PORT in "${PORTS[@]}"; do
    if lsof -i :$PORT >/dev/null 2>&1; then
        echo -e "${RED}WARNING: Port $PORT is in use${NC}"
        lsof -i :$PORT | tail -n +2
        CONFLICTS=$((CONFLICTS + 1))
    fi
done

if [ $CONFLICTS -gt 0 ]; then
    echo ""
    echo -e "${RED}Found $CONFLICTS port conflict(s). Please resolve before continuing.${NC}"
    echo "You can check what's using the ports with: ./scripts/check_ports.sh"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Step 4: Building containers (if needed)...${NC}"
docker-compose build --no-cache

echo ""
echo -e "${YELLOW}Step 5: Starting containers...${NC}"
docker-compose up -d

echo ""
echo -e "${GREEN}✓ Containers started!${NC}"
echo ""
echo "View logs with:"
echo "  docker-compose logs -f"
echo ""
echo "Check status with:"
echo "  docker-compose ps"
echo ""
echo "Stop containers with:"
echo "  docker-compose down"
