"""Phase 1 integration tests for Korean stock user scenario (infra-003).

Verifies the full user journey:
  1. Signup → Login → Dashboard
  2. Search for 삼성전자 → debounce → highlight → add to watchlist → auto-close
  3. Threshold change → success feedback
  4. Empty state when watchlist is empty
  5. Invalid token → error handling
"""
from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_phase1_integration.db"

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
    session.close()


def _teardown() -> None:
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_phase1_integration.db"):
        os.remove("test_phase1_integration.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


# --- Scenario 1: Signup → Login → Access protected endpoint ---


@pytest.mark.asyncio
async def test_signup_login_flow() -> None:
    """User can sign up, log in, and access protected endpoints."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            signup = await c.post("/api/auth/signup", json={
                "email": "phase1@test.com", "password": "testpass123",
            })
            assert signup.status_code in (200, 201)

            login = await c.post("/api/auth/login", json={
                "email": "phase1@test.com", "password": "testpass123",
            })
            assert login.status_code == 200
            tokens = login.json()
            assert "access_token" in tokens
            assert "refresh_token" in tokens

            me = await c.get("/api/me", headers={
                "Authorization": f"Bearer {tokens['access_token']}",
            })
            assert me.status_code == 200
            assert me.json()["email"] == "phase1@test.com"
    finally:
        _teardown()


# --- Scenario 2: Stock search after seed ---


@pytest.mark.asyncio
async def test_search_stocks_returns_results() -> None:
    """Search API returns seeded KRX stocks."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={"q": "삼성"})
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) > 0
            names = [s["name"] for s in data]
            assert any("삼성" in n for n in names)
    finally:
        _teardown()


# --- Scenario 3: Full watchlist journey ---


@pytest.mark.asyncio
async def test_watchlist_add_and_remove() -> None:
    """Authenticated user can add stock to watchlist and remove it."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            await c.post("/api/auth/signup", json={
                "email": "wl@test.com", "password": "testpass123",
            })
            login = await c.post("/api/auth/login", json={
                "email": "wl@test.com", "password": "testpass123",
            })
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            search = await c.get("/api/stocks/search", params={"q": "삼성"})
            stock_id = search.json()[0]["id"]

            add = await c.post("/api/watchlist", json={"stock_id": stock_id}, headers=headers)
            assert add.status_code in (200, 201)
            item_id = add.json()["id"]

            wl = await c.get("/api/watchlist", headers=headers)
            assert wl.status_code == 200
            assert len(wl.json()) == 1

            rm = await c.delete(f"/api/watchlist/{item_id}", headers=headers)
            assert rm.status_code in (200, 204)

            wl2 = await c.get("/api/watchlist", headers=headers)
            assert len(wl2.json()) == 0
    finally:
        _teardown()


# --- Scenario 4: Threshold update ---


@pytest.mark.asyncio
async def test_threshold_update() -> None:
    """User can update watchlist item threshold."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            await c.post("/api/auth/signup", json={
                "email": "th@test.com", "password": "testpass123",
            })
            login = await c.post("/api/auth/login", json={
                "email": "th@test.com", "password": "testpass123",
            })
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            search = await c.get("/api/stocks/search", params={"q": "삼성"})
            stock_id = search.json()[0]["id"]

            add = await c.post("/api/watchlist", json={"stock_id": stock_id}, headers=headers)
            assert add.status_code in (200, 201)
            item_id = add.json()["id"]

            patch = await c.patch(
                f"/api/watchlist/{item_id}",
                json={"threshold": 5.0},
                headers=headers,
            )
            assert patch.status_code == 200
            assert patch.json()["threshold"] == 5.0
    finally:
        _teardown()


# --- Scenario 5: Invalid token returns 401 ---


@pytest.mark.asyncio
async def test_invalid_token_returns_401() -> None:
    """Invalid token should return 401."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/me", headers={
                "Authorization": "Bearer invalid-token-here",
            })
            assert resp.status_code == 401
    finally:
        _teardown()


# --- Frontend integration checks ---


def test_dashboard_page_uses_watchlist_manager():
    """Dashboard page should render WatchlistManager."""
    path = os.path.join(BASE_FE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "WatchlistManager" in content


def test_watchlist_manager_uses_stock_search():
    """WatchlistManager should use StockSearch component."""
    path = os.path.join(BASE_FE, "components", "WatchlistManager.tsx")
    content = open(path).read()
    assert "StockSearch" in content
    assert "StockCard" in content


def test_stock_search_uses_debounce():
    """StockSearch should implement debounce."""
    path = os.path.join(BASE_FE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "DEBOUNCE_MS" in content
    assert "AbortController" in content
    assert "highlightMatch" in content
    assert "RecentSearches" in content


def test_stock_card_has_threshold_settings():
    """StockCard should have threshold settings."""
    path = os.path.join(BASE_FE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "threshold" in content
    assert "settings-icon" in content


def test_layout_has_global_ux():
    """Layout should include ToastContainer and ProgressBar."""
    path = os.path.join(BASE_FE, "app", "layout.tsx")
    content = open(path).read()
    assert "ToastContainer" in content
    assert "ProgressBar" in content


def test_error_boundaries_exist():
    """Both error.tsx and global-error.tsx should exist."""
    assert os.path.isfile(os.path.join(BASE_FE, "app", "error.tsx"))
    assert os.path.isfile(os.path.join(BASE_FE, "app", "global-error.tsx"))
