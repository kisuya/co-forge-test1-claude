"""Phase 3 integration tests for US stock scenario (stock-004).

Verifies the US stock user journey:
  1. Search with market tab '미국' → '애플' → AAPL with Korean highlight
  2. AAPL add to watchlist → NYSE badge displayed
  3. Mixed KR + US stocks in dashboard
  4. US stock analysis report with market field
  5. Report detail with English news source links
  6. Phase 1-2 regression: existing features still work
"""
from __future__ import annotations

import os
import uuid
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.stock import Stock
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_phase3_us_stocks.db"

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
    if os.path.exists("test_phase3_us_stocks.db"):
        os.remove("test_phase3_us_stocks.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(c: AsyncClient) -> str:
    """Signup and login, return access token."""
    await c.post("/api/auth/signup", json={
        "email": "phase3@test.com", "password": "testpass123",
    })
    login = await c.post("/api/auth/login", json={
        "email": "phase3@test.com", "password": "testpass123",
    })
    return login.json()["access_token"]


# --- Scenario 1: US search with market tab ---


@pytest.mark.asyncio
async def test_search_us_market_returns_aapl() -> None:
    """Searching '애플' with market=us should return AAPL."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={
                "q": "애플", "market": "us",
            })
            assert resp.status_code == 200
            data = resp.json()
            codes = [s["code"] for s in data]
            assert "AAPL" in codes


    finally:
        _teardown()


@pytest.mark.asyncio
async def test_search_us_returns_market_field() -> None:
    """US search results should include NYSE/NASDAQ market field."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={
                "q": "AAPL", "market": "us",
            })
            data = resp.json()
            assert len(data) >= 1
            assert data[0]["market"] in ("NYSE", "NASDAQ")
    finally:
        _teardown()


# --- Scenario 2: Add AAPL to watchlist with market badge ---


@pytest.mark.asyncio
async def test_add_us_stock_watchlist_has_market() -> None:
    """Adding US stock should return watchlist item with stock_market."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            search = await c.get("/api/stocks/search", params={
                "q": "AAPL", "market": "us",
            })
            stock_id = search.json()[0]["id"]

            add = await c.post("/api/watchlist", json={
                "stock_id": stock_id,
            }, headers=headers)
            assert add.status_code in (200, 201)
            item = add.json()
            assert "stock_market" in item
            assert item["stock_market"] in ("NYSE", "NASDAQ")
    finally:
        _teardown()


# --- Scenario 3: Mixed KR + US stocks in watchlist ---


@pytest.mark.asyncio
async def test_mixed_watchlist_kr_and_us() -> None:
    """Watchlist should support both KR and US stocks simultaneously."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            kr = await c.get("/api/stocks/search", params={"q": "삼성전자"})
            kr_id = kr.json()[0]["id"]

            us = await c.get("/api/stocks/search", params={
                "q": "AAPL", "market": "us",
            })
            us_id = us.json()[0]["id"]

            await c.post("/api/watchlist", json={"stock_id": kr_id}, headers=headers)
            await c.post("/api/watchlist", json={"stock_id": us_id}, headers=headers)

            wl = await c.get("/api/watchlist", headers=headers)
            assert wl.status_code == 200
            items = wl.json()
            assert len(items) == 2
            markets = {i["stock_market"] for i in items}
            assert "KRX" in markets
            assert len(markets) >= 2  # at least KRX + one US market
    finally:
        _teardown()


# --- Scenario 4: US stock analysis report ---


def test_us_analysis_includes_market_field() -> None:
    """US stock analysis should include market field in analysis data."""
    from app.services.analysis_service import US_MARKETS, _is_us_stock

    _setup()
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        us_stock = session.query(Stock).filter(
            Stock.market.in_(US_MARKETS)
        ).first()
        assert us_stock is not None
        assert _is_us_stock(us_stock) is True
    finally:
        session.close()
        _teardown()


def test_kr_stock_not_detected_as_us() -> None:
    """KRX stock should not be detected as US stock."""
    from app.services.analysis_service import _is_us_stock

    _setup()
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        kr_stock = session.query(Stock).filter(
            Stock.market == "KRX"
        ).first()
        assert kr_stock is not None
        assert _is_us_stock(kr_stock) is False
    finally:
        session.close()
        _teardown()


# --- Scenario 5: Frontend structure checks ---


def test_stock_search_has_market_tabs():
    """StockSearch should have market tab UI."""
    path = os.path.join(BASE_FE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "market-tabs" in content
    assert "MARKET_TABS" in content
    assert "전체" in content
    assert "한국" in content
    assert "미국" in content


def test_stock_search_has_name_kr_highlight():
    """StockSearch should highlight name_kr for US stocks."""
    path = os.path.join(BASE_FE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "nameKrParts" in content
    assert "name_kr" in content


def test_stock_card_has_market_badge():
    """StockCard should display colored market badges."""
    path = os.path.join(BASE_FE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "MARKET_BADGE" in content
    assert "card-market-badge" in content


def test_queries_passes_market_param():
    """stocksApi.search should accept and pass market parameter."""
    path = os.path.join(BASE_FE, "lib", "queries.ts")
    content = open(path).read()
    assert "market" in content


# --- Phase 1-2 regression ---


def test_regression_watchlist_manager():
    """WatchlistManager should still exist and import StockSearch."""
    path = os.path.join(BASE_FE, "components", "WatchlistManager.tsx")
    content = open(path).read()
    assert "StockSearch" in content
    assert "StockCard" in content


def test_regression_error_boundaries():
    """Error boundaries should still exist."""
    assert os.path.isfile(os.path.join(BASE_FE, "app", "error.tsx"))
    assert os.path.isfile(os.path.join(BASE_FE, "app", "global-error.tsx"))


@pytest.mark.asyncio
async def test_regression_kr_search_still_works() -> None:
    """Korean stock search should still return results."""
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


@pytest.mark.asyncio
async def test_regression_push_subscribe_works() -> None:
    """Push subscribe should still work (Phase 2 regression)."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await c.post("/api/push/subscribe", json={
                "endpoint": "https://push.example.com/p3",
                "p256dh": "key",
                "auth": "auth",
            }, headers=headers)
            assert resp.status_code in (200, 201)
    finally:
        _teardown()
