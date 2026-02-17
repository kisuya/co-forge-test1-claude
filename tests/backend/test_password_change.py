"""Tests for password change API (profile-005)."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_password_change.db"


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
    if _os.path.exists("test_password_change.db"):
        _os.remove("test_password_change.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(
    client: AsyncClient, email: str = "pwtest@example.com", password: str = "pass1234"
) -> str:
    await client.post(
        "/api/auth/signup",
        json={"email": email, "password": password},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_password_change_success() -> None:
    """Successful password change allows login with new password."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.put(
                "/api/profile/password",
                json={"current_password": "pass1234", "new_password": "newPass99"},
                headers=headers,
            )
            assert resp.status_code == 200

            # Login with new password succeeds
            login_resp = await client.post(
                "/api/auth/login",
                json={"email": "pwtest@example.com", "password": "newPass99"},
            )
            assert login_resp.status_code == 200
            assert "access_token" in login_resp.json()

            # Login with old password fails
            old_resp = await client.post(
                "/api/auth/login",
                json={"email": "pwtest@example.com", "password": "pass1234"},
            )
            assert old_resp.status_code == 401
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_password_change_wrong_current() -> None:
    """Wrong current password returns 400."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.put(
                "/api/profile/password",
                json={"current_password": "wrongpass", "new_password": "newPass99"},
                headers=headers,
            )

        assert resp.status_code == 400
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_password_change_too_short() -> None:
    """New password shorter than 8 chars returns 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.put(
                "/api/profile/password",
                json={"current_password": "pass1234", "new_password": "short1"},
                headers=headers,
            )

        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_password_change_no_digits() -> None:
    """New password without digits returns 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.put(
                "/api/profile/password",
                json={"current_password": "pass1234", "new_password": "abcdefghij"},
                headers=headers,
            )

        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_password_change_no_letters() -> None:
    """New password without letters returns 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.put(
                "/api/profile/password",
                json={"current_password": "pass1234", "new_password": "12345678"},
                headers=headers,
            )

        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_password_change_requires_auth() -> None:
    """Password change requires authentication."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.put(
                "/api/profile/password",
                json={"current_password": "pass1234", "new_password": "newPass99"},
            )

        assert resp.status_code in (401, 403)
    finally:
        _teardown()
