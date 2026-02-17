"""Shared test fixtures for backend tests."""
from __future__ import annotations

import sys
import os

import pytest

# Ensure backend app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

# Set a secure 32+ byte test key before any app imports
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-ohmystock-must-be-at-least-32-bytes-long",
)


@pytest.fixture(autouse=True)
def _reset_rate_limit_counter() -> None:
    """Reset rate limit counter before each test to prevent cross-test interference."""
    from app.core.rate_limit import counter
    counter.reset()
