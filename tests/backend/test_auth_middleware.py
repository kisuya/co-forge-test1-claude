"""Tests for authentication middleware and route protection."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.user import User

TEST_DB_URL = "sqlite:///test_middleware.db"


def _get_test_db() -> Session:  # type: ignore[misc]
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()


def _setup() -> None:
    create_tables(TEST_DB_URL)


def _teardown() -> None:
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os as _os
    if _os.path.exists("test_middleware.db"):
        _os.remove("test_middleware.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _create_user_and_get_token(client: AsyncClient) -> str:
    """Helper to signup, login, and return access token."""
    await client.post(
        "/api/auth/signup",
        json={"email": "testuser@example.com", "password": "pass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "testuser@example.com", "password": "pass123"},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_protected_endpoint_without_token_returns_401() -> None:
    """GET /api/me without Authorization header should return 401/403."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/me")
        assert resp.status_code in (401, 403)
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token_returns_401() -> None:
    """GET /api/me with invalid token should return 401."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/me",
                headers={"Authorization": "Bearer invalid.token.here"},
            )
        assert resp.status_code == 401
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token_returns_user() -> None:
    """GET /api/me with valid access token should return user info."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _create_user_and_get_token(client)
            resp = await client.get(
                "/api/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "testuser@example.com"
        assert "id" in data
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_protected_endpoint_with_refresh_token_returns_401() -> None:
    """GET /api/me with refresh token (not access) should return 401."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/signup",
                json={"email": "refresh@example.com", "password": "pass123"},
            )
            login_resp = await client.post(
                "/api/auth/login",
                json={"email": "refresh@example.com", "password": "pass123"},
            )
            refresh_token = login_resp.json()["refresh_token"]
            resp = await client.get(
                "/api/me",
                headers={"Authorization": f"Bearer {refresh_token}"},
            )
        assert resp.status_code == 401
    finally:
        _teardown()
