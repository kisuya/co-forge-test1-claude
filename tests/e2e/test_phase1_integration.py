"""Phase 1-3 integration tests (infra-004).

Verifies:
  1. API error → CORS headers present
  2. Invalid report_id → 404 + standard error format
  3. Dashboard StockCard → price + change + tracking count
  4. StockCard ⋮ menu → threshold/alert actions
  5. Stock detail → /stocks/{id} → event timeline + pagination
  6. Empty history → empty state UI
  7. Mobile: bottom sheet menu structure
  8. Regression: search, watchlist CRUD, alert settings
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import PriceSnapshot, Report
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_phase1_integration_v2.db"

BASE_FE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


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
    seed_us_stocks(session)
    session.close()


def _teardown() -> None:
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_phase1_integration_v2.db"):
        os.remove("test_phase1_integration_v2.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(c: AsyncClient, email: str = "phase1v2@test.com") -> str:
    await c.post("/api/auth/signup", json={"email": email, "password": "testpass123"})
    login = await c.post("/api/auth/login", json={"email": email, "password": "testpass123"})
    return login.json()["access_token"]


# --- Scenario 1: CORS headers on error responses ---


@pytest.mark.asyncio
async def test_cors_headers_on_404() -> None:
    """404 responses should include CORS headers."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get(
                "/api/nonexistent-endpoint",
                headers={"Origin": "http://localhost:3000"},
            )
            assert resp.status_code == 404
            assert "access-control-allow-origin" in resp.headers
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_cors_headers_on_422() -> None:
    """Validation error responses should include CORS headers."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post(
                "/api/auth/signup",
                json={},
                headers={"Origin": "http://localhost:3000"},
            )
            assert resp.status_code == 422
            assert "access-control-allow-origin" in resp.headers
    finally:
        _teardown()


# --- Scenario 2: Standard error format ---


@pytest.mark.asyncio
async def test_error_format_standard() -> None:
    """Error responses follow standard {error, message, status_code} format."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            fake_uuid = str(uuid.uuid4())
            resp = await c.get(f"/api/reports/{fake_uuid}", headers=headers)
            assert resp.status_code == 404
            data = resp.json()
            assert "error" in data
            assert "message" in data
            assert "status_code" in data
            assert data["status_code"] == 404
    finally:
        _teardown()


# --- Scenario 3: Watchlist with price data ---


@pytest.mark.asyncio
async def test_watchlist_includes_price_fields() -> None:
    """GET /api/watchlist should include price and tracking fields."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            search = await c.get("/api/stocks/search", params={"q": "삼성"})
            stock_id = search.json()[0]["id"]

            await c.post("/api/watchlist", json={"stock_id": stock_id}, headers=headers)

            wl = await c.get("/api/watchlist", headers=headers)
            assert wl.status_code == 200
            items = wl.json()
            assert len(items) >= 1
            item = items[0]
            assert "is_price_available" in item
            assert "price_freshness" in item
            assert "tracking_count" in item
            assert item["tracking_count"] >= 1
    finally:
        _teardown()


# --- Scenario 4: Threshold and alert toggle ---


@pytest.mark.asyncio
async def test_threshold_update_and_alert_toggle() -> None:
    """User can update threshold and toggle alerts on watchlist item."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c, "threshold@test.com")
            headers = {"Authorization": f"Bearer {token}"}

            search = await c.get("/api/stocks/search", params={"q": "삼성"})
            stock_id = search.json()[0]["id"]

            add = await c.post("/api/watchlist", json={"stock_id": stock_id}, headers=headers)
            item_id = add.json()["id"]

            # Update threshold
            patch = await c.patch(
                f"/api/watchlist/{item_id}",
                json={"threshold": 5.0},
                headers=headers,
            )
            assert patch.status_code == 200
            assert patch.json()["threshold"] == 5.0

            # Toggle alert
            alert_resp = await c.patch(
                f"/api/watchlist/{item_id}",
                json={"alert_enabled": False},
                headers=headers,
            )
            assert alert_resp.status_code == 200
    finally:
        _teardown()


# --- Scenario 5: Stock detail and event history ---


@pytest.mark.asyncio
async def test_stock_detail_and_history() -> None:
    """Stock detail API and history API work together."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c, "history@test.com")
            headers = {"Authorization": f"Bearer {token}"}

            search = await c.get("/api/stocks/search", params={"q": "삼성전자"})
            stocks = search.json()
            stock_id = stocks[0]["id"]

            # Add to watchlist first
            await c.post("/api/watchlist", json={"stock_id": stock_id}, headers=headers)

            # Stock detail
            detail = await c.get(f"/api/stocks/{stock_id}", headers=headers)
            assert detail.status_code == 200
            detail_data = detail.json()
            assert "name" in detail_data
            assert "tracking_count" in detail_data
            assert detail_data["is_tracked_by_me"] is True

            # History (empty)
            history = await c.get(f"/api/stocks/{stock_id}/history", headers=headers)
            assert history.status_code == 200
            history_data = history.json()
            assert "events" in history_data
            assert isinstance(history_data["events"], list)
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stock_detail_not_tracked() -> None:
    """Stock detail shows is_tracked_by_me=false when not tracked."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c, "nottrack@test.com")
            headers = {"Authorization": f"Bearer {token}"}

            search = await c.get("/api/stocks/search", params={"q": "삼성전자"})
            stock_id = search.json()[0]["id"]

            detail = await c.get(f"/api/stocks/{stock_id}", headers=headers)
            assert detail.status_code == 200
            assert detail.json()["is_tracked_by_me"] is False
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stock_detail_404() -> None:
    """Non-existent stock_id returns 404."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c, "notfound@test.com")
            headers = {"Authorization": f"Bearer {token}"}

            fake_uuid = str(uuid.uuid4())
            resp = await c.get(f"/api/stocks/{fake_uuid}", headers=headers)
            assert resp.status_code == 404
    finally:
        _teardown()


# --- Scenario 6: Empty history UI verification ---


def test_timeline_component_has_empty_state():
    """EventTimeline component should handle empty state."""
    path = os.path.join(BASE_FE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert "추적 이벤트가 없습니다" in content or "이벤트가 없습니다" in content


def test_timeline_component_has_pagination():
    """EventTimeline should have load more button."""
    path = os.path.join(BASE_FE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert "더 보기" in content or "load-more" in content


# --- Scenario 7: Mobile bottom sheet structure ---


def test_stockcard_has_bottomsheet():
    """StockCard should have bottom sheet for mobile."""
    path = os.path.join(BASE_FE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "bottom-sheet" in content or "bottomsheet" in content or "BottomSheet" in content


def test_stockcard_has_kebab_menu():
    """StockCard should have kebab menu."""
    path = os.path.join(BASE_FE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "kebab" in content or "kebab-menu" in content


def test_stockcard_has_price_display():
    """StockCard should display price data."""
    path = os.path.join(BASE_FE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "latest_price" in content or "latestPrice" in content
    assert "price_change" in content or "priceChange" in content


# --- Scenario 8: Regression tests ---


@pytest.mark.asyncio
async def test_regression_signup_login() -> None:
    """Signup and login should still work."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            signup = await c.post("/api/auth/signup", json={
                "email": "regress@test.com", "password": "testpass123",
            })
            assert signup.status_code in (200, 201)

            login = await c.post("/api/auth/login", json={
                "email": "regress@test.com", "password": "testpass123",
            })
            assert login.status_code == 200
            assert "access_token" in login.json()
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_regression_watchlist_crud() -> None:
    """Watchlist CRUD should still work."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c, "wlcrud@test.com")
            headers = {"Authorization": f"Bearer {token}"}

            search = await c.get("/api/stocks/search", params={"q": "삼성"})
            stock_id = search.json()[0]["id"]

            add = await c.post("/api/watchlist", json={"stock_id": stock_id}, headers=headers)
            assert add.status_code in (200, 201)
            item_id = add.json()["id"]

            wl = await c.get("/api/watchlist", headers=headers)
            assert len(wl.json()) == 1

            rm = await c.delete(f"/api/watchlist/{item_id}", headers=headers)
            assert rm.status_code in (200, 204)

            wl2 = await c.get("/api/watchlist", headers=headers)
            assert len(wl2.json()) == 0
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_regression_stock_search() -> None:
    """Stock search for KR and US should still work."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            kr = await c.get("/api/stocks/search", params={"q": "삼성"})
            assert kr.status_code == 200
            assert len(kr.json()) > 0

            us = await c.get("/api/stocks/search", params={"q": "AAPL", "market": "us"})
            assert us.status_code == 200
            assert len(us.json()) >= 1
    finally:
        _teardown()


def test_regression_watchlist_manager_exists():
    """WatchlistManager component should exist."""
    path = os.path.join(BASE_FE, "components", "WatchlistManager.tsx")
    assert os.path.isfile(path)


def test_regression_stock_search_component():
    """StockSearch component should exist with debounce."""
    path = os.path.join(BASE_FE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "DEBOUNCE_MS" in content


def test_regression_error_boundaries():
    """Error boundaries should exist."""
    assert os.path.isfile(os.path.join(BASE_FE, "app", "error.tsx"))
    assert os.path.isfile(os.path.join(BASE_FE, "app", "global-error.tsx"))


# --- Frontend structure checks for stock detail ---


def test_stock_detail_page_exists():
    """Stock detail page route should exist."""
    path = os.path.join(BASE_FE, "app", "stocks", "[stockId]", "page.tsx")
    assert os.path.isfile(path)


def test_stock_detail_page_has_timeline():
    """Stock detail page should use EventTimeline."""
    path = os.path.join(BASE_FE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert "EventTimeline" in content


def test_stock_detail_page_has_discussions():
    """Stock detail page should include DiscussionSection."""
    path = os.path.join(BASE_FE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert "DiscussionSection" in content


def test_stock_detail_loading_skeleton():
    """Stock detail page should have loading skeleton."""
    path = os.path.join(BASE_FE, "app", "stocks", "[stockId]", "loading.tsx")
    assert os.path.isfile(path)
