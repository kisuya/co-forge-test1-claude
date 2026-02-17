"""Tests for shared report public access API (share-003)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import Report, ReportSource
from app.models.shared_report import SharedReport
from app.models.stock import Stock
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_share_public.db"


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
    if _os.path.exists("test_share_public.db"):
        _os.remove("test_share_public.db")


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
        json={"email": "pubshare@example.com", "password": "pass1234"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "pubshare@example.com", "password": "pass1234"},
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


def _create_report_with_share(
    db_url: str, stock_id: uuid.UUID, user_id: uuid.UUID,
    expired: bool = False,
) -> tuple[uuid.UUID, str]:
    """Create a report and shared report, return (report_id, share_token)."""
    factory = get_session_factory(db_url)
    session = factory()
    report = Report(
        stock_id=stock_id,
        trigger_price=Decimal("50000"),
        trigger_change_pct=5.0,
        status="completed",
        summary="반도체 실적 호조로 상승",
        analysis={
            "summary": "반도체 실적 호조로 상승",
            "causes": [{"cause": "실적 발표", "description": "3분기 영업이익 증가"}],
            "similar_cases": [{"case": "2025 반도체 호황"}],
        },
    )
    session.add(report)
    session.flush()

    # Add a source
    source = ReportSource(
        report_id=report.id,
        source_type="news",
        title="반도체 관련 뉴스",
        url="https://example.com/news/1",
    )
    session.add(source)

    expires = datetime.now(timezone.utc) + timedelta(days=30)
    if expired:
        expires = datetime(2020, 1, 1, tzinfo=timezone.utc)

    shared = SharedReport(
        report_id=report.id,
        created_by=user_id,
        expires_at=expires,
    )
    session.add(shared)
    session.commit()

    rid = report.id
    token = shared.share_token
    session.close()
    return rid, token


@pytest.mark.asyncio
async def test_shared_report_valid_token() -> None:
    """GET /api/shared/{token} returns report data without auth."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            me = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
            user_id = uuid.UUID(me.json()["id"])

        _, share_token = _create_report_with_share(TEST_DB_URL, stock.id, user_id)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # No auth header - public access
            resp = await client.get(f"/api/shared/{share_token}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["stock_name"] == stock.name
        assert data["stock_code"] == stock.code
        assert data["market"] == stock.market
        assert data["report"]["summary"] == "반도체 실적 호조로 상승"
        assert len(data["report"]["causes"]) == 1
        assert len(data["report"]["sources"]) == 1
        assert data["report"]["sources"][0]["title"] == "반도체 관련 뉴스"
        assert "shared_at" in data
        assert "expires_at" in data
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_shared_report_expired_token() -> None:
    """GET /api/shared/{expired_token} returns 410 Gone."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            me = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
            user_id = uuid.UUID(me.json()["id"])

        _, share_token = _create_report_with_share(
            TEST_DB_URL, stock.id, user_id, expired=True,
        )

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/shared/{share_token}")

        assert resp.status_code == 410
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_shared_report_invalid_token() -> None:
    """GET /api/shared/{invalid} returns 404."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/shared/invalid-token-xyz")

        assert resp.status_code == 404
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_shared_report_no_personal_info() -> None:
    """Shared report response does not contain user personal info."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            me = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
            user_id = uuid.UUID(me.json()["id"])

        _, share_token = _create_report_with_share(TEST_DB_URL, stock.id, user_id)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/shared/{share_token}")

        assert resp.status_code == 200
        data_str = resp.text
        # No user_id or email in response
        assert "pubshare@example.com" not in data_str
        assert str(user_id) not in data_str
    finally:
        _teardown()
