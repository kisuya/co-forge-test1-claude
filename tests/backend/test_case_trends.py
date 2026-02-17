"""Tests for case trend data and API (case-002)."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import PriceSnapshot, Report
from app.models.stock import Stock
from app.services.similar_case_service import (
    TREND_1M_DAYS,
    TREND_1W_DAYS,
    SimilarCaseWithTrend,
    TrendPoint,
    _get_trend_after,
    get_cases_with_trends,
)

TEST_DB_URL = "sqlite:///test_case_trends.db"


def _setup() -> Session:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    return factory()


def _teardown(session: Session) -> None:
    session.close()
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_case_trends.db"):
        os.remove("test_case_trends.db")


def _add_stock(session: Session) -> Stock:
    stock = Stock(code="005930", name="삼성전자", market="KRX")
    session.add(stock)
    session.flush()
    return stock


def _add_snapshot(
    session: Session, stock: Stock, change_pct: float, days_ago: int,
    price: Decimal = Decimal("50000"), volume: int = 100000,
) -> PriceSnapshot:
    snap = PriceSnapshot(
        stock_id=stock.id, price=price, change_pct=change_pct,
        volume=volume, captured_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    session.add(snap)
    session.flush()
    return snap


# --- Constants ---


def test_trend_1w_days():
    assert TREND_1W_DAYS == 5


def test_trend_1m_days():
    assert TREND_1M_DAYS == 20


# --- TrendPoint dataclass ---


def test_trend_point_fields():
    tp = TrendPoint(day=1, change_pct=1.5)
    assert tp.day == 1
    assert tp.change_pct == 1.5


# --- _get_trend_after ---


def test_get_trend_no_data():
    """No snapshots after event → empty trend."""
    session = _setup()
    try:
        stock = _add_stock(session)
        session.commit()
        result = _get_trend_after(session, stock.id, datetime.utcnow(), 5)
        assert result == []
    finally:
        _teardown(session)


def test_get_trend_returns_points():
    """Should return cumulative change points from base price."""
    session = _setup()
    try:
        stock = _add_stock(session)
        event_date = datetime.utcnow() - timedelta(days=60)
        for i in range(5):
            _add_snapshot(
                session, stock, 0.5,
                days_ago=59 - i,
                price=Decimal("50000") + Decimal(str(i * 500)),
            )
        session.commit()
        result = _get_trend_after(session, stock.id, event_date, 5)
        assert len(result) == 5
        assert result[0].day == 1
        assert result[0].change_pct == 0.0  # base price
        assert result[4].day == 5
    finally:
        _teardown(session)


def test_get_trend_limited_by_max_days():
    """Should return at most max_days points."""
    session = _setup()
    try:
        stock = _add_stock(session)
        event_date = datetime.utcnow() - timedelta(days=60)
        for i in range(30):
            _add_snapshot(session, stock, 0.5, days_ago=59 - i)
        session.commit()
        result = _get_trend_after(session, stock.id, event_date, 5)
        assert len(result) <= 5
    finally:
        _teardown(session)


# --- SimilarCaseWithTrend ---


def test_similar_case_with_trend_fields():
    case = SimilarCaseWithTrend(
        date=datetime.utcnow(), change_pct=5.0, volume=100000,
        similarity_score=0.5, trend_1w=[], trend_1m=[], data_insufficient=True,
    )
    assert case.data_insufficient is True
    assert case.trend_1w == []


# --- get_cases_with_trends ---


def test_get_cases_with_trends_empty():
    """Empty DB → empty list."""
    session = _setup()
    try:
        stock = _add_stock(session)
        session.commit()
        result = get_cases_with_trends(session, str(stock.id), 5.0)
        assert result == []
    finally:
        _teardown(session)


def test_get_cases_with_trends_returns_trends():
    """Cases should have trend_1w and trend_1m data."""
    session = _setup()
    try:
        stock = _add_stock(session)
        # Old event
        _add_snapshot(session, stock, 5.0, days_ago=60, price=Decimal("50000"))
        # Trend data after event
        for i in range(10):
            _add_snapshot(
                session, stock, 0.5, days_ago=59 - i,
                price=Decimal("50000") + Decimal(str(i * 100)),
            )
        session.commit()
        result = get_cases_with_trends(session, str(stock.id), 5.0)
        assert len(result) >= 1
        assert len(result[0].trend_1w) > 0
    finally:
        _teardown(session)


def test_get_cases_insufficient_flag():
    """data_insufficient should be True when trend_1w has < 5 points."""
    session = _setup()
    try:
        stock = _add_stock(session)
        _add_snapshot(session, stock, 5.0, days_ago=60, price=Decimal("50000"))
        # Only 2 days of trend data
        _add_snapshot(session, stock, 0.5, days_ago=59, price=Decimal("50500"))
        _add_snapshot(session, stock, 0.3, days_ago=58, price=Decimal("51000"))
        session.commit()
        result = get_cases_with_trends(session, str(stock.id), 5.0)
        assert len(result) >= 1
        assert result[0].data_insufficient is True
    finally:
        _teardown(session)


# --- API endpoint ---


def _get_test_db() -> Session:  # type: ignore[misc]
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(c: AsyncClient) -> str:
    await c.post("/api/auth/signup", json={
        "email": "trends@test.com", "password": "testpass123",
    })
    login = await c.post("/api/auth/login", json={
        "email": "trends@test.com", "password": "testpass123",
    })
    return login.json()["access_token"]


@pytest.mark.asyncio
async def test_api_cases_no_report() -> None:
    """GET /api/cases/{missing_id} should return 404 (quality-002)."""
    create_tables(TEST_DB_URL)
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            fake_id = str(uuid.uuid4())
            resp = await c.get(f"/api/cases/{fake_id}", headers=headers)
            assert resp.status_code == 404
    finally:
        engine = get_engine(TEST_DB_URL)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        if os.path.exists("test_case_trends.db"):
            os.remove("test_case_trends.db")


@pytest.mark.asyncio
async def test_api_cases_with_report() -> None:
    """GET /api/cases/{report_id} should return cases for existing report."""
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    db_session = factory()
    try:
        stock = Stock(code="005930", name="삼성전자", market="KRX")
        db_session.add(stock)
        db_session.flush()

        # Old similar snapshot
        old_snap = PriceSnapshot(
            stock_id=stock.id, price=Decimal("50000"),
            change_pct=5.0, volume=100000,
            captured_at=datetime.utcnow() - timedelta(days=60),
        )
        db_session.add(old_snap)

        report = Report(
            stock_id=stock.id, trigger_price=Decimal("55000"),
            trigger_change_pct=5.2, status="completed",
        )
        db_session.add(report)
        db_session.commit()
        report_id = str(report.id)
        db_session.close()

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await c.get(f"/api/cases/{report_id}", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["cases"]) >= 1
            case = data["cases"][0]
            assert "change_pct" in case
            assert "similarity_score" in case
            assert "trend_1w" in case
            assert "trend_1m" in case
    finally:
        engine = get_engine(TEST_DB_URL)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        if os.path.exists("test_case_trends.db"):
            os.remove("test_case_trends.db")


@pytest.mark.asyncio
async def test_api_cases_requires_auth() -> None:
    """GET /api/cases/{id} should require authentication."""
    create_tables(TEST_DB_URL)
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get(f"/api/cases/{uuid.uuid4()}")
            assert resp.status_code in (401, 403)
    finally:
        engine = get_engine(TEST_DB_URL)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        if os.path.exists("test_case_trends.db"):
            os.remove("test_case_trends.db")


def test_cases_router_registered():
    """cases_router should be registered in main.py."""
    import importlib
    mod = importlib.import_module("app.main")
    src = open(mod.__file__).read()
    assert "cases_router" in src
