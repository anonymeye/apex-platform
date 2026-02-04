#!/bin/bash
# Script to create the initial Alembic migration

cd "$(dirname "$0")/.." || exit

# Create initial migration
alembic revision --autogenerate -m "Initial migration: users, organizations, and memberships"

echo "Migration created! Review the migration file in migrations/versions/ before running:"
echo "  alembic upgrade head"
