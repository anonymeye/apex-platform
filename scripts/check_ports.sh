#!/bin/bash
# Port conflict checker for Apex services

echo "=== Checking Port Conflicts ==="
echo ""

PORTS=(5432 8000 3000)
PORT_NAMES=("PostgreSQL" "Apex API" "Portal Frontend")

for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}
    
    echo -n "Port $PORT ($NAME): "
    
    if lsof -i :$PORT >/dev/null 2>&1; then
        echo -e "\033[0;33mIN USE\033[0m"
        echo "  Processes using port $PORT:"
        lsof -i :$PORT | tail -n +2 | awk '{print "    - PID", $2, ":", $1}'
    else
        echo -e "\033[0;32mAVAILABLE\033[0m"
    fi
    echo ""
done

echo "=== Docker Container Status ==="
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}" | grep -E "apex|postgres|portal|NAMES" || echo "No Apex containers running"
