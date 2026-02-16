"""Tests for push subscription API (alert-001)."""
from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.push_subscription import PushSubscription

TEST_DB_URL = "sqlite:///test_api_push.db"


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
    if os.path.exists("test_api_push.db"):
        os.remove("test_api_push.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.api.push import get_db as push_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    app.dependency_overrides[push_get_db] = _get_test_db
    return app


async def _signup_and_login(c: AsyncClient) -> str:
    """Helper: signup + login and return access token."""
    await c.post("/api/auth/signup", json={
        "email": "push@test.com", "password": "testpass123",
    })
    login = await c.post("/api/auth/login", json={
        "email": "push@test.com", "password": "testpass123",
    })
    return login.json()["access_token"]


# --- Model structure ---


def test_push_subscription_model_fields() -> None:
    """PushSubscription should have required fields."""
    cols = {c.name for c in PushSubscription.__table__.columns}
    assert "id" in cols
    assert "user_id" in cols
    assert "endpoint" in cols
    assert "p256dh" in cols
    assert "auth" in cols
    assert "is_active" in cols
    assert "created_at" in cols


def test_push_subscription_endpoint_unique() -> None:
    """PushSubscription endpoint should be unique."""
    col = PushSubscription.__table__.c.endpoint
    assert col.unique is True


# --- VAPID config ---


def test_vapid_settings_exist() -> None:
    """Settings should have VAPID fields."""
    from app.config import Settings
    s = Settings()
    assert hasattr(s, "vapid_public_key")
    assert hasattr(s, "vapid_private_key")
    assert hasattr(s, "vapid_contact")


# --- POST /api/push/subscribe ---


@pytest.mark.asyncio
async def test_subscribe_requires_auth() -> None:
    """Subscribe endpoint should return 401 without token."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/api/push/subscribe", json={
                "endpoint": "https://push.example.com/sub1",
                "p256dh": "key123",
                "auth": "auth123",
            })
            assert resp.status_code in (401, 403)
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_subscribe_creates_subscription() -> None:
    """Subscribe should create a new push subscription."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_and_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await c.post("/api/push/subscribe", json={
                "endpoint": "https://push.example.com/sub1",
                "p256dh": "key123",
                "auth": "auth123",
            }, headers=headers)
            assert resp.status_code == 201
            data = resp.json()
            assert data["endpoint"] == "https://push.example.com/sub1"
            assert data["is_active"] is True
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_subscribe_upsert_same_endpoint() -> None:
    """Re-subscribing same endpoint should update (upsert), not create duplicate."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_and_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            await c.post("/api/push/subscribe", json={
                "endpoint": "https://push.example.com/sub1",
                "p256dh": "key123",
                "auth": "auth123",
            }, headers=headers)

            resp2 = await c.post("/api/push/subscribe", json={
                "endpoint": "https://push.example.com/sub1",
                "p256dh": "newkey456",
                "auth": "newauth456",
            }, headers=headers)
            assert resp2.status_code == 201
            assert resp2.json()["is_active"] is True

            status = await c.get("/api/push/status", headers=headers)
            assert status.json()["endpoint_count"] == 1
    finally:
        _teardown()


# --- DELETE /api/push/unsubscribe ---


@pytest.mark.asyncio
async def test_unsubscribe_deactivates() -> None:
    """Unsubscribe should set is_active=false (soft delete)."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_and_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            await c.post("/api/push/subscribe", json={
                "endpoint": "https://push.example.com/sub1",
                "p256dh": "key123",
                "auth": "auth123",
            }, headers=headers)

            resp = await c.request("DELETE", "/api/push/unsubscribe", json={
                "endpoint": "https://push.example.com/sub1",
            }, headers=headers)
            assert resp.status_code == 200
            assert resp.json()["status"] == "unsubscribed"

            status = await c.get("/api/push/status", headers=headers)
            assert status.json()["subscribed"] is False
            assert status.json()["endpoint_count"] == 0
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_unsubscribe_not_found() -> None:
    """Unsubscribe non-existent endpoint should return 404."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_and_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await c.request("DELETE", "/api/push/unsubscribe", json={
                "endpoint": "https://push.example.com/nonexistent",
            }, headers=headers)
            assert resp.status_code == 404
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_unsubscribe_requires_auth() -> None:
    """Unsubscribe endpoint should return 401 without token."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.request("DELETE", "/api/push/unsubscribe", json={
                "endpoint": "https://push.example.com/sub1",
            })
            assert resp.status_code in (401, 403)
    finally:
        _teardown()


# --- GET /api/push/status ---


@pytest.mark.asyncio
async def test_status_no_subscriptions() -> None:
    """Status should return subscribed=false when no subscriptions."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_and_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await c.get("/api/push/status", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["subscribed"] is False
            assert data["endpoint_count"] == 0
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_status_with_subscription() -> None:
    """Status should return subscribed=true with count after subscribing."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_and_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            await c.post("/api/push/subscribe", json={
                "endpoint": "https://push.example.com/sub1",
                "p256dh": "key1",
                "auth": "auth1",
            }, headers=headers)
            await c.post("/api/push/subscribe", json={
                "endpoint": "https://push.example.com/sub2",
                "p256dh": "key2",
                "auth": "auth2",
            }, headers=headers)

            resp = await c.get("/api/push/status", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["subscribed"] is True
            assert data["endpoint_count"] == 2
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_status_requires_auth() -> None:
    """Status endpoint should return 401 without token."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/push/status")
            assert resp.status_code in (401, 403)
    finally:
        _teardown()
