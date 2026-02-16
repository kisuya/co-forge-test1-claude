"""Tests for authentication API endpoints."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.user import User

TEST_DB_URL = "sqlite:///test_auth.db"


def _get_test_db() -> Session:  # type: ignore[misc]
    """Override get_db for tests."""
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
    if _os.path.exists("test_auth.db"):
        _os.remove("test_auth.db")


def _make_app():  # type: ignore[no-untyped-def]
    """Create a test app with overridden DB dependency."""
    from app.api.auth import get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = _get_test_db
    return app


@pytest.mark.asyncio
async def test_signup_success_returns_201() -> None:
    """POST /api/auth/signup with valid data should return 201."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/auth/signup",
                json={"email": "new@example.com", "password": "securepass123"},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert "id" in data
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_signup_duplicate_email_returns_409() -> None:
    """POST /api/auth/signup with existing email should return 409."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/signup",
                json={"email": "dup@example.com", "password": "pass1"},
            )
            resp = await client.post(
                "/api/auth/signup",
                json={"email": "dup@example.com", "password": "pass2"},
            )
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"].lower()
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_signup_stores_hashed_password() -> None:
    """Signup should store bcrypt-hashed password, not plain text."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/signup",
                json={"email": "hash@example.com", "password": "mypassword"},
            )

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        from sqlalchemy import select
        user = session.execute(
            select(User).where(User.email == "hash@example.com")
        ).scalar_one()
        session.close()

        assert user.password_hash != "mypassword"
        assert user.password_hash.startswith("$2")
    finally:
        _teardown()
