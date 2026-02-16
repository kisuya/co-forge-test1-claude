"""Tests for stock data seed and search API."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.stock import Stock
from app.services.stock_service import search_stocks, seed_stocks

TEST_DB_URL = "sqlite:///test_stocks.db"


def _get_test_db() -> Session:  # type: ignore[misc]
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()


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
    import os as _os
    if _os.path.exists("test_stocks.db"):
        _os.remove("test_stocks.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


def test_seed_stocks_inserts_records() -> None:
    """seed_stocks should insert sample KRX stocks."""
    session = _setup()
    try:
        count = seed_stocks(session)
        assert count > 0
        stocks = session.query(Stock).all()
        assert len(stocks) == count
    finally:
        _teardown(session)


def test_seed_stocks_is_idempotent() -> None:
    """Running seed_stocks twice should not create duplicates."""
    session = _setup()
    try:
        count1 = seed_stocks(session)
        count2 = seed_stocks(session)
        assert count2 == 0
        stocks = session.query(Stock).all()
        assert len(stocks) == count1
    finally:
        _teardown(session)


def test_search_stocks_by_name() -> None:
    """search_stocks should find stocks by Korean name."""
    session = _setup()
    try:
        seed_stocks(session)
        results = search_stocks(session, "삼성")
        assert len(results) >= 1
        assert any("삼성" in s.name for s in results)
    finally:
        _teardown(session)


def test_search_stocks_by_code() -> None:
    """search_stocks should find stocks by code."""
    session = _setup()
    try:
        seed_stocks(session)
        results = search_stocks(session, "005930")
        assert len(results) == 1
        assert results[0].name == "삼성전자"
    finally:
        _teardown(session)


@pytest.mark.asyncio
async def test_search_api_returns_results() -> None:
    """GET /api/stocks/search?q=삼성 should return matching stocks."""
    session = _setup()
    try:
        seed_stocks(session)
        session.close()

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/stocks/search", params={"q": "삼성"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert any("삼성" in s["name"] for s in data)
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_search_api_empty_query_returns_422() -> None:
    """GET /api/stocks/search without query should return 422."""
    session = _setup()
    try:
        session.close()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/stocks/search")
        assert resp.status_code == 422
    finally:
        _teardown()
