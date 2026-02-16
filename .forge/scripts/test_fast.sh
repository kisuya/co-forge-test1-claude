#!/bin/bash
# Fast test runner for oh-my-stock (Python backend + Node frontend)
set -e

FAIL=0

# Backend tests (if exists)
if [ -d "backend" ] && [ -d "tests/backend" ]; then
  echo "--- Backend tests ---"
  cd backend
  python -m pytest ../tests/backend/ -x -q "$@" || FAIL=1
  cd ..
fi

# Smoke tests (always run)
if [ -f "tests/test_smoke.py" ]; then
  echo "--- Smoke tests ---"
  python -m pytest tests/test_smoke.py -x -q || FAIL=1
fi

# Frontend tests (if exists)
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
  echo "--- Frontend tests ---"
  cd frontend
  npx vitest run --bail 2>/dev/null || FAIL=1
  cd ..
fi

exit $FAIL
