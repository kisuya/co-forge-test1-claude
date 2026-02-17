"""Tests for user profile API (profile-001)."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_profile_api.db"


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
    if _os.path.exists("test_profile_api.db"):
        _os.remove("test_profile_api.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(client: AsyncClient, email: str = "profile@example.com") -> str:
    await client.post(
        "/api/auth/signup",
        json={"email": email, "password": "pass1234"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "pass1234"},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_profile_get() -> None:
    """GET /api/profile returns profile with display_name from email."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get("/api/profile", headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "profile@example.com"
        assert data["nickname"] is None
        assert data["display_name"] == "profile"  # email prefix
        assert "created_at" in data
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_profile_set_nickname() -> None:
    """PUT /api/profile sets nickname."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.put(
                "/api/profile",
                json={"nickname": "테스트유저"},
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["nickname"] == "테스트유저"
        assert data["display_name"] == "테스트유저"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_profile_change_nickname() -> None:
    """Changing nickname updates correctly."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            await client.put(
                "/api/profile",
                json={"nickname": "first_name"},
                headers=headers,
            )
            resp = await client.put(
                "/api/profile",
                json={"nickname": "second_name"},
                headers=headers,
            )

        assert resp.status_code == 200
        assert resp.json()["nickname"] == "second_name"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_profile_duplicate_nickname_409() -> None:
    """Duplicate nickname returns 409."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            t1 = await _signup_login(client, "user1@example.com")
            t2 = await _signup_login(client, "user2@example.com")

            # User 1 sets nickname
            await client.put(
                "/api/profile",
                json={"nickname": "unique_nick"},
                headers={"Authorization": f"Bearer {t1}"},
            )

            # User 2 tries same nickname
            resp = await client.put(
                "/api/profile",
                json={"nickname": "unique_nick"},
                headers={"Authorization": f"Bearer {t2}"},
            )

        assert resp.status_code == 409
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_profile_invalid_nickname_422() -> None:
    """Invalid nickname pattern returns 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # Too short
            resp1 = await client.put(
                "/api/profile",
                json={"nickname": "a"},
                headers=headers,
            )

            # Special chars
            resp2 = await client.put(
                "/api/profile",
                json={"nickname": "hello world!"},
                headers=headers,
            )

        assert resp1.status_code == 422
        assert resp2.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_profile_reset_nickname_to_null() -> None:
    """Setting nickname to null/empty restores display_name to email prefix."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # Set nickname
            await client.put(
                "/api/profile",
                json={"nickname": "test_user"},
                headers=headers,
            )

            # Reset to null
            resp = await client.put(
                "/api/profile",
                json={"nickname": None},
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["nickname"] is None
        assert data["display_name"] == "profile"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_profile_reset_nickname_to_empty() -> None:
    """Setting nickname to empty string resets to null."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            await client.put(
                "/api/profile",
                json={"nickname": "test_user"},
                headers=headers,
            )

            resp = await client.put(
                "/api/profile",
                json={"nickname": ""},
                headers=headers,
            )

        assert resp.status_code == 200
        assert resp.json()["nickname"] is None
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_profile_requires_auth() -> None:
    """Profile endpoints require authentication."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/profile")

        assert resp.status_code in (401, 403)
    finally:
        _teardown()
