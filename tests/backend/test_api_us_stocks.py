"""Tests for US stock search and registration API (stock-003)."""
from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_api_us_stocks.db"


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
    if os.path.exists("test_api_us_stocks.db"):
        os.remove("test_api_us_stocks.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


# --- market query parameter ---


@pytest.mark.asyncio
async def test_search_default_market_is_kr() -> None:
    """Default search (no market param) returns only KRX stocks."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={"q": "삼성"})
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) > 0
            for stock in data:
                assert stock["market"] == "KRX"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_search_market_us_returns_us_only() -> None:
    """market=us should return only NYSE/NASDAQ stocks."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={"q": "Apple", "market": "us"})
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) > 0
            for stock in data:
                assert stock["market"] in ("NYSE", "NASDAQ")
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_search_market_all_returns_both() -> None:
    """market=all should return both KRX and US stocks if query matches."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={"q": "S", "market": "all"})
            assert resp.status_code == 200
            data = resp.json()
            markets = {s["market"] for s in data}
            assert len(markets) > 0
    finally:
        _teardown()


# --- Korean name search ---


@pytest.mark.asyncio
async def test_search_korean_name_returns_us_stock() -> None:
    """Searching '애플' with market=us should return AAPL."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={"q": "애플", "market": "us"})
            assert resp.status_code == 200
            data = resp.json()
            codes = [s["code"] for s in data]
            assert "AAPL" in codes
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_search_tesla_korean() -> None:
    """Searching '테슬라' with market=us should return TSLA."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={"q": "테슬라", "market": "us"})
            assert resp.status_code == 200
            data = resp.json()
            codes = [s["code"] for s in data]
            assert "TSLA" in codes
    finally:
        _teardown()


# --- English search ---


@pytest.mark.asyncio
async def test_search_by_code_aapl() -> None:
    """Searching 'AAPL' with market=us should return Apple."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={"q": "AAPL", "market": "us"})
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) >= 1
            assert data[0]["code"] == "AAPL"
    finally:
        _teardown()


# --- Backward compatibility ---


@pytest.mark.asyncio
async def test_kr_search_backward_compat() -> None:
    """Existing search without market param should still return KRX results."""
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


@pytest.mark.asyncio
async def test_us_search_does_not_return_krx() -> None:
    """market=us search should not return KRX stocks."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={"q": "삼성", "market": "us"})
            assert resp.status_code == 200
            data = resp.json()
            for stock in data:
                assert stock["market"] != "KRX"
    finally:
        _teardown()


# --- US stock in watchlist ---


@pytest.mark.asyncio
async def test_add_us_stock_to_watchlist() -> None:
    """User can add US stock to watchlist via existing POST /api/watchlist."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            await c.post("/api/auth/signup", json={
                "email": "usstock@test.com", "password": "testpass123",
            })
            login = await c.post("/api/auth/login", json={
                "email": "usstock@test.com", "password": "testpass123",
            })
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            search = await c.get("/api/stocks/search", params={"q": "AAPL", "market": "us"})
            assert search.status_code == 200
            stock_id = search.json()[0]["id"]

            add = await c.post("/api/watchlist", json={"stock_id": stock_id}, headers=headers)
            assert add.status_code in (200, 201)

            wl = await c.get("/api/watchlist", headers=headers)
            assert wl.status_code == 200
            assert len(wl.json()) == 1
    finally:
        _teardown()


# --- Response includes market field ---


@pytest.mark.asyncio
async def test_search_response_includes_market() -> None:
    """Search response should include market field for differentiation."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={"q": "NVDA", "market": "us"})
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) >= 1
            assert "market" in data[0]
            assert data[0]["market"] in ("NYSE", "NASDAQ")
    finally:
        _teardown()
