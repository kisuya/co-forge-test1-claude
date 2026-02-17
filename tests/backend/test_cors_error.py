"""Tests for CORS headers on error responses (quality-001)."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app, ALLOWED_ORIGINS

ALLOWED_ORIGIN = "http://localhost:3000"
DISALLOWED_ORIGIN = "http://evil.example.com"


def _make_app():
    """Create a test app with a route that raises a 500 error."""
    app = create_app()

    @app.get("/api/test-500")
    async def trigger_500():
        raise RuntimeError("Intentional server error for testing")

    return app


@pytest.mark.asyncio
async def test_404_includes_cors_headers() -> None:
    """A request to a non-existent endpoint should return 404 with CORS headers."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/nonexistent",
            headers={"Origin": ALLOWED_ORIGIN},
        )
    assert resp.status_code == 404
    assert resp.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN
    assert "GET" in resp.headers.get("access-control-allow-methods", "")


@pytest.mark.asyncio
async def test_422_validation_error_includes_cors_headers() -> None:
    """A validation error (422) should include CORS headers."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # POST to signup with missing fields to trigger validation error
        resp = await client.post(
            "/api/auth/signup",
            json={},
            headers={"Origin": ALLOWED_ORIGIN},
        )
    assert resp.status_code == 422
    assert resp.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN
    assert "GET" in resp.headers.get("access-control-allow-methods", "")


@pytest.mark.asyncio
async def test_500_server_error_includes_cors_headers() -> None:
    """A 500 server error should include CORS headers."""
    app = _make_app()
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/test-500",
            headers={"Origin": ALLOWED_ORIGIN},
        )
    assert resp.status_code == 500
    assert resp.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN


@pytest.mark.asyncio
async def test_options_preflight_returns_200_with_cors() -> None:
    """OPTIONS preflight should return 200 with CORS headers."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.options(
            "/api/auth/signup",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            },
        )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN


@pytest.mark.asyncio
async def test_disallowed_origin_no_cors_headers() -> None:
    """Requests from disallowed origins should not get CORS allow-origin."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/nonexistent",
            headers={"Origin": DISALLOWED_ORIGIN},
        )
    assert resp.status_code == 404
    # Disallowed origin should not appear in access-control-allow-origin
    allow_origin = resp.headers.get("access-control-allow-origin", "")
    assert DISALLOWED_ORIGIN not in allow_origin


@pytest.mark.asyncio
async def test_401_unauthorized_includes_cors_headers() -> None:
    """A 401 Unauthorized should include CORS headers."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/me",
            headers={"Origin": ALLOWED_ORIGIN},
        )
    assert resp.status_code in (401, 403)
    assert resp.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN


@pytest.mark.asyncio
async def test_error_response_json_format() -> None:
    """Error responses should have consistent JSON format with 'detail' key."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/nonexistent",
            headers={"Origin": ALLOWED_ORIGIN},
        )
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
