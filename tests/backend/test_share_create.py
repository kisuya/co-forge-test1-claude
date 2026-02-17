"""Tests for report sharing URL creation API (share-002)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import Report
from app.models.shared_report import SharedReport
from app.models.stock import Stock
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_share_create.db"


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
    if _os.path.exists("test_share_create.db"):
        _os.remove("test_share_create.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(client: AsyncClient, email: str = "sharetest@example.com") -> str:
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


def _create_report(db_url: str, stock_id: uuid.UUID) -> uuid.UUID:
    factory = get_session_factory(db_url)
    session = factory()
    report = Report(
        stock_id=stock_id,
        trigger_price=Decimal("50000"),
        trigger_change_pct=5.0,
        status="completed",
        summary="Test report",
        analysis={"summary": "Test", "causes": []},
    )
    session.add(report)
    session.commit()
    rid = report.id
    session.close()
    return rid


@pytest.mark.asyncio
async def test_share_creation() -> None:
    """POST /api/reports/{id}/share creates a share link."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        report_id = _create_report(TEST_DB_URL, stock.id)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # Add stock to watchlist first
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )

            # Create share
            resp = await client.post(
                f"/api/reports/{report_id}/share", headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "share_token" in data
        assert len(data["share_token"]) == 36
        assert data["share_url"] == f"/shared/{data['share_token']}"
        assert "expires_at" in data
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_share_duplicate_returns_existing() -> None:
    """Duplicate share request returns existing valid token."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        report_id = _create_report(TEST_DB_URL, stock.id)

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

            resp1 = await client.post(
                f"/api/reports/{report_id}/share", headers=headers,
            )
            resp2 = await client.post(
                f"/api/reports/{report_id}/share", headers=headers,
            )

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        # Same token returned
        assert resp1.json()["share_token"] == resp2.json()["share_token"]
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_share_403_untracked_stock() -> None:
    """Cannot share report for stock not in user's watchlist."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        report_id = _create_report(TEST_DB_URL, stock.id)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # Don't add to watchlist - direct share attempt
            resp = await client.post(
                f"/api/reports/{report_id}/share", headers=headers,
            )

        assert resp.status_code == 403
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_share_404_nonexistent_report() -> None:
    """Share for nonexistent report returns 404."""
    _setup()
    try:
        fake_id = str(uuid.uuid4())
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.post(
                f"/api/reports/{fake_id}/share", headers=headers,
            )

        assert resp.status_code == 404
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_share_expires_at_30_days() -> None:
    """Share expires_at is 30 days from creation."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        report_id = _create_report(TEST_DB_URL, stock.id)

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

            resp = await client.post(
                f"/api/reports/{report_id}/share", headers=headers,
            )

        assert resp.status_code == 200
        expires_at_str = resp.json()["expires_at"]
        # Parse the expires_at
        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = expires_at - now
        assert 29 <= diff.days <= 30
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_share_expired_token_creates_new() -> None:
    """If existing token is expired, a new one is created."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        report_id = _create_report(TEST_DB_URL, stock.id)

        # Manually create an expired shared report
        from sqlalchemy import select
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

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

            # Get user_id from /api/me
            me_resp = await client.get("/api/me", headers=headers)
            user_id = uuid.UUID(me_resp.json()["id"])

        # Insert expired shared report
        expired = SharedReport(
            report_id=report_id,
            created_by=user_id,
            expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        session.add(expired)
        session.commit()
        old_token = expired.share_token
        session.close()

        # Request share - should create new since old is expired
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login_resp = await client.post(
                "/api/auth/login",
                json={"email": "sharetest@example.com", "password": "pass1234"},
            )
            jwt_token = login_resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {jwt_token}"}

            resp = await client.post(
                f"/api/reports/{report_id}/share", headers=headers,
            )

        assert resp.status_code == 200
        new_token = resp.json()["share_token"]
        assert new_token != old_token
    finally:
        _teardown()
