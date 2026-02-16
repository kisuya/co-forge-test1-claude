"""Tests for report API endpoints."""
from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import Report, ReportSource
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_reports_api.db"


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
    if _os.path.exists("test_reports_api.db"):
        _os.remove("test_reports_api.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(client: AsyncClient) -> str:
    await client.post(
        "/api/auth/signup",
        json={"email": "reporter@example.com", "password": "pass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "reporter@example.com", "password": "pass123"},
    )
    return resp.json()["access_token"]


def _create_report_data() -> None:
    """Create a stock, watchlist, and completed report in the test DB."""
    factory = get_session_factory(TEST_DB_URL)
    session = factory()

    samsung = session.execute(
        select(Stock).where(Stock.code == "005930")
    ).scalar_one()

    user = session.execute(
        select(User).where(User.email == "reporter@example.com")
    ).scalar_one_or_none()

    if user is not None:
        wl = Watchlist(user_id=user.id, stock_id=samsung.id, threshold=3.0)
        session.add(wl)

        report = Report(
            stock_id=samsung.id,
            trigger_price=Decimal("70000"),
            trigger_change_pct=-5.0,
            summary="삼성전자 급락 분석",
            analysis={"causes": [{"reason": "실적 부진", "confidence": "high", "impact": "하락"}]},
            status="completed",
        )
        session.add(report)
        session.flush()

        source = ReportSource(
            report_id=report.id,
            source_type="news",
            title="삼성전자 실적 뉴스",
            url="https://news.example.com/1",
        )
        session.add(source)
        session.commit()
    session.close()


@pytest.mark.asyncio
async def test_list_reports_returns_user_reports() -> None:
    """GET /api/reports should return reports for user's watchlist."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            _create_report_data()

            resp = await client.get("/api/reports", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["stock_name"] == "삼성전자"
        assert data[0]["status"] == "completed"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_get_report_by_id() -> None:
    """GET /api/reports/{id} should return report details."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            _create_report_data()

            list_resp = await client.get("/api/reports", headers=headers)
            report_id = list_resp.json()[0]["id"]

            resp = await client.get(f"/api/reports/{report_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"] == "삼성전자 급락 분석"
        assert len(data["sources"]) == 1
        assert data["analysis"]["causes"][0]["confidence"] == "high"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_get_reports_by_stock() -> None:
    """GET /api/reports/stock/{stock_id} should return stock's reports."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            _create_report_data()

            list_resp = await client.get("/api/reports", headers=headers)
            stock_id = list_resp.json()[0]["stock_id"]

            resp = await client.get(
                f"/api/reports/stock/{stock_id}", headers=headers
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_reports_require_auth() -> None:
    """Accessing reports without auth should return 401/403."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/reports")
        assert resp.status_code in (401, 403)
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_get_nonexistent_report_returns_404() -> None:
    """GET /api/reports/{id} with invalid ID should return 404."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            import uuid
            fake_id = str(uuid.uuid4())
            resp = await client.get(f"/api/reports/{fake_id}", headers=headers)
        assert resp.status_code == 404
    finally:
        _teardown()
