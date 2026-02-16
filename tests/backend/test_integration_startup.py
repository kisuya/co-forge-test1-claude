"""Tests for service startup: seed_stocks auto-run, CORS, and search integration."""
from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.main import ALLOWED_ORIGINS, _run_seed
from app.models.stock import Stock
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_integration_startup.db"


def _setup() -> Session:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    return factory()


def _teardown(session: Session | None = None) -> None:
    if session:
        session.close()
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_integration_startup.db"):
        os.remove("test_integration_startup.db")


def _get_test_db() -> Session:  # type: ignore[misc]
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


# --- Seed auto-run on startup ---


def test_run_seed_populates_stocks() -> None:
    """_run_seed should create tables and seed KRX stocks."""
    try:
        _run_seed(TEST_DB_URL)
        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        stocks = session.query(Stock).all()
        assert len(stocks) >= 20
        session.close()
    finally:
        _teardown()


def test_run_seed_idempotent() -> None:
    """Running _run_seed twice should not duplicate data."""
    try:
        _run_seed(TEST_DB_URL)
        _run_seed(TEST_DB_URL)
        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        stocks = session.query(Stock).all()
        assert len(stocks) >= 20
        codes = [s.code for s in stocks]
        assert len(codes) == len(set(codes)), "Duplicate stock codes found"
        session.close()
    finally:
        _teardown()


def test_seed_on_empty_db_only() -> None:
    """seed_stocks inserts only when stocks table is empty for each code."""
    session = _setup()
    try:
        count1 = seed_stocks(session)
        assert count1 > 0
        count2 = seed_stocks(session)
        assert count2 == 0, "seed_stocks should skip when data exists"
    finally:
        _teardown(session)


# --- CORS middleware ---


def test_cors_allows_localhost_3000() -> None:
    """CORS should allow http://localhost:3000."""
    assert "http://localhost:3000" in ALLOWED_ORIGINS


def test_cors_allows_production_origin() -> None:
    """CORS should allow production origins."""
    assert "https://ohmystock.kr" in ALLOWED_ORIGINS
    assert "https://www.ohmystock.kr" in ALLOWED_ORIGINS


def test_cors_allows_127_0_0_1() -> None:
    """CORS should allow http://127.0.0.1:3000."""
    assert "http://127.0.0.1:3000" in ALLOWED_ORIGINS


@pytest.mark.asyncio
async def test_cors_header_in_response() -> None:
    """Response should include Access-Control-Allow-Origin for localhost."""
    session = _setup()
    try:
        seed_stocks(session)
        session.close()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.get(
                "/health",
                headers={"Origin": "http://localhost:3000"},
            )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
    finally:
        _teardown()


# --- Search integration after seed ---


@pytest.mark.asyncio
async def test_search_samsung_after_seed() -> None:
    """After seed, /api/stocks/search?q=삼성 should return results."""
    session = _setup()
    try:
        seed_stocks(session)
        session.close()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/stocks/search", params={"q": "삼성"}
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1, "Search for 삼성 should return results"
        assert any("삼성" in s["name"] for s in data)
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_search_by_code_after_seed() -> None:
    """After seed, searching by code should return the stock."""
    session = _setup()
    try:
        seed_stocks(session)
        session.close()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/stocks/search", params={"q": "005930"}
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "삼성전자"
        assert data[0]["market"] == "KRX"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_all_seeded_stocks_have_krx_market() -> None:
    """All seeded stocks should have market=KRX."""
    session = _setup()
    try:
        seed_stocks(session)
        stocks = session.query(Stock).all()
        for stock in stocks:
            assert stock.market == "KRX", f"{stock.code} has wrong market"
    finally:
        _teardown(session)
