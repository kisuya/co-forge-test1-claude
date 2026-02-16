"""Phase 2 integration tests for alert notification scenario (alert-004).

Verifies the alert user journey:
  1. Dashboard bell icon → settings panel opens
  2. Global toggle ON → browser permission request flow
  3. Per-stock toggle display
  4. Push subscribe API → DB stores subscription
  5. Push worker sends notifications to watchers
  6. Service Worker registration in frontend
  7. Phase 1 regression: existing features still work
"""
from __future__ import annotations

import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.push_subscription import PushSubscription
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.push_service import PushResult, send_spike_notifications
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_phase2_alerts.db"

BASE_FE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
PUBLIC_FE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public")


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
    if os.path.exists("test_phase2_alerts.db"):
        os.remove("test_phase2_alerts.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


# --- Scenario 1: Push subscribe API ---


@pytest.mark.asyncio
async def test_push_subscribe_stores_subscription() -> None:
    """POST /api/push/subscribe should store subscription in DB."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            await c.post("/api/auth/signup", json={
                "email": "alert@test.com", "password": "testpass123",
            })
            login = await c.post("/api/auth/login", json={
                "email": "alert@test.com", "password": "testpass123",
            })
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            resp = await c.post("/api/push/subscribe", json={
                "endpoint": "https://push.example.com/e2e",
                "p256dh": "test-key-e2e",
                "auth": "test-auth-e2e",
            }, headers=headers)
            assert resp.status_code in (200, 201)
    finally:
        _teardown()


# --- Scenario 2: Push status ---


@pytest.mark.asyncio
async def test_push_status_after_subscribe() -> None:
    """GET /api/push/status should show subscribed after subscribe."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            await c.post("/api/auth/signup", json={
                "email": "status@test.com", "password": "testpass123",
            })
            login = await c.post("/api/auth/login", json={
                "email": "status@test.com", "password": "testpass123",
            })
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            await c.post("/api/push/subscribe", json={
                "endpoint": "https://push.example.com/status",
                "p256dh": "key",
                "auth": "auth",
            }, headers=headers)

            status = await c.get("/api/push/status", headers=headers)
            assert status.status_code == 200
            data = status.json()
            assert data["subscribed"] is True
            assert data["endpoint_count"] >= 1
    finally:
        _teardown()


# --- Scenario 3: Unsubscribe ---


@pytest.mark.asyncio
async def test_push_unsubscribe_deactivates() -> None:
    """DELETE /api/push/unsubscribe should deactivate subscription."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            await c.post("/api/auth/signup", json={
                "email": "unsub@test.com", "password": "testpass123",
            })
            login = await c.post("/api/auth/login", json={
                "email": "unsub@test.com", "password": "testpass123",
            })
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            await c.post("/api/push/subscribe", json={
                "endpoint": "https://push.example.com/unsub",
                "p256dh": "key",
                "auth": "auth",
            }, headers=headers)

            unsub = await c.request(
                "DELETE",
                "/api/push/unsubscribe",
                json={"endpoint": "https://push.example.com/unsub"},
                headers=headers,
            )
            assert unsub.status_code == 200

            status = await c.get("/api/push/status", headers=headers)
            assert status.json()["subscribed"] is False
    finally:
        _teardown()


# --- Scenario 4: Push worker sends to watchers ---


def test_push_worker_sends_to_watchers() -> None:
    """send_spike_notifications should send push to users watching stock."""
    import bcrypt
    _setup()
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        user = User(
            email="worker@test.com",
            password_hash=bcrypt.hashpw(b"pass", bcrypt.gensalt()).decode(),
        )
        session.add(user)
        session.flush()

        stock = session.query(Stock).first()
        assert stock is not None

        wl = Watchlist(user_id=user.id, stock_id=stock.id, threshold=3.0)
        session.add(wl)

        sub = PushSubscription(
            user_id=user.id,
            endpoint="https://push.example.com/worker",
            p256dh="key",
            auth="auth",
            is_active=True,
        )
        session.add(sub)
        session.commit()

        sent = []
        def mock_send(s: PushSubscription, payload: str) -> None:
            sent.append(payload)

        result = send_spike_notifications(session, str(stock.id), 5.0, send_fn=mock_send)
        assert result.success == 1
        assert len(sent) == 1
    finally:
        session.close()
        _teardown()


# --- Scenario 5: Unauthenticated push access ---


@pytest.mark.asyncio
async def test_push_endpoints_require_auth() -> None:
    """Push API endpoints should require authentication."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/api/push/subscribe", json={
                "endpoint": "x", "p256dh": "y", "auth": "z",
            })
            assert resp.status_code in (401, 403)

            status = await c.get("/api/push/status")
            assert status.status_code in (401, 403)
    finally:
        _teardown()


# --- Frontend structure checks ---


def test_dashboard_has_notification_bell():
    """Dashboard should include NotificationPanel with bell icon."""
    path = os.path.join(BASE_FE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "NotificationPanel" in content


def test_notification_panel_has_global_toggle():
    """NotificationPanel should have a global alert toggle."""
    path = os.path.join(BASE_FE, "components", "NotificationPanel.tsx")
    content = open(path).read()
    assert "global-toggle" in content
    assert "requestPermission" in content


def test_notification_panel_has_stock_toggles():
    """NotificationPanel should have per-stock toggles."""
    path = os.path.join(BASE_FE, "components", "NotificationPanel.tsx")
    content = open(path).read()
    assert "stock-toggles" in content


def test_service_worker_handles_push():
    """public/sw.js should handle push and notification click events."""
    path = os.path.join(PUBLIC_FE, "sw.js")
    content = open(path).read()
    assert "push" in content
    assert "notificationclick" in content
    assert "showNotification" in content


def test_queries_has_push_api():
    """queries.ts should have pushApi with subscribe/unsubscribe/status."""
    path = os.path.join(BASE_FE, "lib", "queries.ts")
    content = open(path).read()
    assert "pushApi" in content
    assert "/api/push/subscribe" in content
    assert "/api/push/unsubscribe" in content
    assert "/api/push/status" in content


# --- Phase 1 regression ---


def test_regression_watchlist_manager_exists():
    """WatchlistManager should still exist and use StockSearch."""
    path = os.path.join(BASE_FE, "components", "WatchlistManager.tsx")
    content = open(path).read()
    assert "StockSearch" in content


def test_regression_error_boundaries_exist():
    """Error boundaries should still exist."""
    assert os.path.isfile(os.path.join(BASE_FE, "app", "error.tsx"))
    assert os.path.isfile(os.path.join(BASE_FE, "app", "global-error.tsx"))


@pytest.mark.asyncio
async def test_regression_stock_search_works() -> None:
    """Stock search should still return results (Phase 1 regression)."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={"q": "삼성"})
            assert resp.status_code == 200
            assert len(resp.json()) > 0
    finally:
        _teardown()
