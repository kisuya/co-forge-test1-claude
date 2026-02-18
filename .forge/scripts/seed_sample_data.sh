#!/bin/bash
# Seed sample data for development/testing.
# Usage: .forge/scripts/seed_sample_data.sh
#
# Supports two modes:
# 1. Docker (default): docker exec into PostgreSQL container
# 2. Python: use SQLAlchemy ORM directly
#
# Set DATABASE_URL env var to override the default connection.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default to Python-based seeding (more robust, handles bcrypt hashing)
echo "=== oh-my-stock: Seeding sample data ==="

cd "$PROJECT_ROOT/backend"

# Use the backend's Python environment
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python"
fi

export DATABASE_URL="${DATABASE_URL:-postgresql://user:pass@localhost:5432/ohmystock}"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-dev-secret-key-for-ohmystock-must-be-at-least-32-bytes-long}"

$PYTHON -m app.scripts.seed_sample_data

echo "=== Seed complete ==="
