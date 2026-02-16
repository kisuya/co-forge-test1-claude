"""Tests for FastAPI application startup and health endpoint."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_200() -> None:
    """GET /health should return 200 with status ok."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_app_has_title() -> None:
    """App should have the correct title."""
    from app.main import app

    assert app.title == "oh-my-stock"
