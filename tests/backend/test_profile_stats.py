"""Tests for profile activity stats API (profile-002)."""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import Report
from app.models.stock import Stock
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_profile_stats.db"


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
    if _os.path.exists("test_profile_stats.db"):
        _os.remove("test_profile_stats.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(client: AsyncClient, email: str = "stats@example.com") -> str:
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
    from sqlalchemy import select
    factory = get_session_factory(db_url)
    session = factory()
    stock = session.execute(
        select(Stock).where(Stock.code == code)
    ).scalar_one()
    session.close()
    return stock


def _create_completed_reports(db_url: str, stock_id: uuid.UUID, count: int) -> None:
    factory = get_session_factory(db_url)
    session = factory()
    for _ in range(count):
        report = Report(
            stock_id=stock_id,
            trigger_price=Decimal("50000"),
            trigger_change_pct=5.0,
            status="completed",
            summary="Test",
        )
        session.add(report)
    session.commit()
    session.close()


@pytest.mark.asyncio
async def test_stats_all_zeros() -> None:
    """New user with no activity has all stats at 0."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get("/api/profile", headers=headers)

        assert resp.status_code == 200
        stats = resp.json()["stats"]
        assert stats["watchlist_count"] == 0
        assert stats["report_count"] == 0
        assert stats["discussion_count"] == 0
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stats_accuracy() -> None:
    """Stats reflect correct counts for watchlist and reports."""
    _setup()
    try:
        samsung = _get_stock_by_code(TEST_DB_URL, "005930")
        sk = _get_stock_by_code(TEST_DB_URL, "000660")
        naver = _get_stock_by_code(TEST_DB_URL, "035420")

        # Create completed reports for these stocks
        _create_completed_reports(TEST_DB_URL, samsung.id, 3)
        _create_completed_reports(TEST_DB_URL, sk.id, 2)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # Add 3 stocks to watchlist
            for stock in [samsung, sk, naver]:
                await client.post(
                    "/api/watchlist",
                    json={"stock_id": str(stock.id)},
                    headers=headers,
                )

            resp = await client.get("/api/profile", headers=headers)

        assert resp.status_code == 200
        stats = resp.json()["stats"]
        assert stats["watchlist_count"] == 3
        # Samsung (3) + SK (2) = 5 reports for watched stocks
        assert stats["report_count"] == 5
        # No discussions yet
        assert stats["discussion_count"] == 0
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stats_excludes_pending_reports() -> None:
    """Report count only includes completed reports."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        # 2 completed, 1 pending
        for status in ["completed", "completed", "pending"]:
            report = Report(
                stock_id=stock.id,
                trigger_price=Decimal("50000"),
                trigger_change_pct=5.0,
                status=status,
                summary="Test",
            )
            session.add(report)
        session.commit()
        session.close()

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )

            resp = await client.get("/api/profile", headers=headers)

        assert resp.status_code == 200
        assert resp.json()["stats"]["report_count"] == 2
    finally:
        _teardown()
