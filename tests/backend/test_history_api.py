"""Tests for event history API (history-001)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import Report
from app.models.stock import Stock
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_history_api.db"


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
    import os as _os
    if _os.path.exists("test_history_api.db"):
        _os.remove("test_history_api.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(client: AsyncClient, email: str = "histtest@example.com") -> str:
    await client.post(
        "/api/auth/signup",
        json={"email": email, "password": "pass1234"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "pass1234"},
    )
    return resp.json()["access_token"]


def _get_stock_by_code(db_url: str, code: str) -> Stock:
    factory = get_session_factory(db_url)
    session = factory()
    from sqlalchemy import select
    stock = session.execute(
        select(Stock).where(Stock.code == code)
    ).scalar_one()
    session.close()
    return stock


def _add_report(
    db_url: str, stock_id: uuid.UUID, change_pct: float,
    status: str = "completed",
    analysis: dict | None = None,
    summary: str | None = None,
    created_at: datetime | None = None,
) -> uuid.UUID:
    """Insert a Report directly into the DB."""
    factory = get_session_factory(db_url)
    session = factory()
    report = Report(
        stock_id=stock_id,
        trigger_price=Decimal("50000"),
        trigger_change_pct=change_pct,
        status=status,
        analysis=analysis,
        summary=summary,
    )
    if created_at:
        report.created_at = created_at
    if status == "completed":
        report.completed_at = created_at or datetime.now(timezone.utc)
    session.add(report)
    session.commit()
    rid = report.id
    session.close()
    return rid


def _add_watchlist(db_url: str, user_id: uuid.UUID, stock_id: uuid.UUID) -> None:
    """Insert a Watchlist item directly."""
    factory = get_session_factory(db_url)
    session = factory()
    item = Watchlist(user_id=user_id, stock_id=stock_id, threshold=3.0)
    session.add(item)
    session.commit()
    session.close()


@pytest.mark.asyncio
async def test_history_with_events() -> None:
    """GET /api/stocks/{id}/history returns events for completed reports."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        _add_report(
            TEST_DB_URL, stock.id, 5.2,
            analysis={"summary": "반도체 실적 호조", "confidence": "high"},
            created_at=datetime(2026, 2, 15, tzinfo=timezone.utc),
        )
        _add_report(
            TEST_DB_URL, stock.id, -3.1,
            analysis={"summary": "미중 무역분쟁 우려", "confidence": "medium"},
            created_at=datetime(2026, 2, 10, tzinfo=timezone.utc),
        )

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(
                f"/api/stocks/{stock.id}/history", headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["stock_id"] == str(stock.id)
        assert data["stock_name"] == stock.name
        assert data["stock_code"] == stock.code
        assert data["market"] == stock.market
        assert len(data["events"]) == 2

        # Most recent first
        ev0 = data["events"][0]
        assert ev0["change_pct"] == 5.2
        assert ev0["direction"] == "up"
        assert ev0["summary"] == "반도체 실적 호조"
        assert ev0["confidence"] == "high"
        assert ev0["date"] == "2026-02-15"

        ev1 = data["events"][1]
        assert ev1["change_pct"] == -3.1
        assert ev1["direction"] == "down"
        assert ev1["summary"] == "미중 무역분쟁 우려"
        assert ev1["confidence"] == "medium"

        assert data["pagination"]["page"] == 1
        assert data["pagination"]["total"] == 2
        assert data["pagination"]["has_more"] is False
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_history_empty() -> None:
    """GET /api/stocks/{id}/history returns empty events with message."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(
                f"/api/stocks/{stock.id}/history", headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["events"] == []
        assert data["message"] == "아직 추적 이벤트가 없습니다"
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["has_more"] is False
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_history_pagination() -> None:
    """History API supports pagination with 21 items -> 2 pages."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        for i in range(21):
            _add_report(
                TEST_DB_URL, stock.id, 2.0 + i * 0.1,
                analysis={"summary": f"이벤트 {i}"},
                created_at=datetime(2026, 1, 1 + i, tzinfo=timezone.utc),
            )

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # Page 1
            resp1 = await client.get(
                f"/api/stocks/{stock.id}/history?page=1&per_page=20",
                headers=headers,
            )
            # Page 2
            resp2 = await client.get(
                f"/api/stocks/{stock.id}/history?page=2&per_page=20",
                headers=headers,
            )

        assert resp1.status_code == 200
        d1 = resp1.json()
        assert len(d1["events"]) == 20
        assert d1["pagination"]["total"] == 21
        assert d1["pagination"]["has_more"] is True

        assert resp2.status_code == 200
        d2 = resp2.json()
        assert len(d2["events"]) == 1
        assert d2["pagination"]["has_more"] is False
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_history_404_nonexistent_stock() -> None:
    """GET /api/stocks/{invalid}/history returns 404."""
    _setup()
    try:
        fake_id = str(uuid.uuid4())
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(
                f"/api/stocks/{fake_id}/history", headers=headers,
            )

        assert resp.status_code == 404
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_history_tracking_since() -> None:
    """tracking_since reflects the earliest watchlist entry."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")

        # Create user and add watchlist
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # Add to watchlist first
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )

            resp = await client.get(
                f"/api/stocks/{stock.id}/history", headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        # tracking_since should be set since we added it to watchlist
        assert data["tracking_since"] is not None
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_history_excludes_pending_reports() -> None:
    """Only completed reports appear in history."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        _add_report(TEST_DB_URL, stock.id, 5.0, status="completed")
        _add_report(TEST_DB_URL, stock.id, 3.0, status="pending")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(
                f"/api/stocks/{stock.id}/history", headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["change_pct"] == 5.0
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_history_requires_auth() -> None:
    """History endpoint requires authentication."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/stocks/{stock.id}/history")

        assert resp.status_code in (401, 403)
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_history_uses_report_summary_fallback() -> None:
    """When analysis has no summary, use report.summary."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        _add_report(
            TEST_DB_URL, stock.id, 4.0,
            analysis=None, summary="직접 입력한 요약",
        )

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(
                f"/api/stocks/{stock.id}/history", headers=headers,
            )

        assert resp.status_code == 200
        ev = resp.json()["events"][0]
        assert ev["summary"] == "직접 입력한 요약"
    finally:
        _teardown()
