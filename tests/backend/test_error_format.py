"""Tests for standardized API error response format (quality-003)."""
from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_error_format.db"


def _get_test_db() -> Session:  # type: ignore[misc]
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()


def _setup() -> None:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    seed_stocks(session)
    session.close()


def _teardown() -> None:
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os as _os
    if _os.path.exists("test_error_format.db"):
        _os.remove("test_error_format.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(client: AsyncClient) -> str:
    await client.post(
        "/api/auth/signup",
        json={"email": "errfmt@example.com", "password": "pass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "errfmt@example.com", "password": "pass123"},
    )
    return resp.json()["access_token"]


def _assert_standard_format(data: dict, expected_status: int) -> None:
    """Assert the response follows standard error format."""
    assert "error" in data, f"Missing 'error' key in response: {data}"
    assert "message" in data, f"Missing 'message' key in response: {data}"
    assert "status_code" in data, f"Missing 'status_code' key in response: {data}"
    assert data["status_code"] == expected_status


@pytest.mark.asyncio
async def test_401_unauthorized_format() -> None:
    """401 errors should use standard format."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/auth/login",
                json={"email": "noone@example.com", "password": "wrong"},
            )
        assert resp.status_code == 401
        _assert_standard_format(resp.json(), 401)
        assert resp.json()["error"] == "Unauthorized"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_404_not_found_format() -> None:
    """404 errors should use standard format."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            fake_id = str(uuid.uuid4())
            resp = await client.get(
                f"/api/reports/{fake_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 404
        _assert_standard_format(resp.json(), 404)
        assert resp.json()["error"] == "NotFound"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_409_conflict_format() -> None:
    """409 Conflict errors should use standard format."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Signup first
            await client.post(
                "/api/auth/signup",
                json={"email": "dup@example.com", "password": "pass123"},
            )
            # Duplicate signup
            resp = await client.post(
                "/api/auth/signup",
                json={"email": "dup@example.com", "password": "pass123"},
            )
        assert resp.status_code == 409
        _assert_standard_format(resp.json(), 409)
        assert resp.json()["error"] == "Conflict"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_422_validation_error_format() -> None:
    """422 Validation errors should use standard format."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/auth/signup",
                json={},
            )
        assert resp.status_code == 422
        data = resp.json()
        _assert_standard_format(data, 422)
        assert data["error"] == "ValidationError"
        assert "details" in data  # Validation errors also include details array
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_500_server_error_format() -> None:
    """500 server errors should use standard format."""
    app = _make_app()

    @app.get("/api/test-500-fmt")
    async def trigger_500():
        raise RuntimeError("test error")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/test-500-fmt")
    assert resp.status_code == 500
    _assert_standard_format(resp.json(), 500)
    assert resp.json()["error"] == "InternalServerError"


@pytest.mark.asyncio
async def test_cases_422_standard_format() -> None:
    """Cases API 422 errors should use standard format."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            resp = await client.get(
                "/api/cases/invalid-id",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 422
        _assert_standard_format(resp.json(), 422)
    finally:
        _teardown()
