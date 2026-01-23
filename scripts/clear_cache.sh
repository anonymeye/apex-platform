#!/bin/bash
# Clear Python cache in container

echo "Clearing Python cache..."
find /workspace/apex/src -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find /workspace/apex/src -name "*.pyc" -delete 2>/dev/null || true
find /workspace/apex/src -name "*.pyo" -delete 2>/dev/null || true
echo "Cache cleared!"
