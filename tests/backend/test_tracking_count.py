"""Tests for tracking count in watchlist API (ui-012)."""
from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_tracking_count.db"


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
    if _os.path.exists("test_tracking_count.db"):
        _os.remove("test_tracking_count.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(client: AsyncClient, email: str, password: str = "pass1234") -> str:
    await client.post(
        "/api/auth/signup",
        json={"email": email, "password": password},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
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


@pytest.mark.asyncio
async def test_tracking_count_single_user() -> None:
    """Single user tracking a stock should show tracking_count=1."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client, "track1@example.com")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )
            resp = await client.get("/api/watchlist", headers=headers)

        assert resp.status_code == 200
        item = resp.json()[0]
        assert item["tracking_count"] == 1
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_tracking_count_multiple_users() -> None:
    """Multiple users tracking same stock shows correct count."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # User 1 adds stock
            token1 = await _signup_login(client, "track_a@example.com")
            headers1 = {"Authorization": f"Bearer {token1}"}
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers1,
            )

            # User 2 adds same stock
            token2 = await _signup_login(client, "track_b@example.com")
            headers2 = {"Authorization": f"Bearer {token2}"}
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers2,
            )

            # User 3 adds same stock
            token3 = await _signup_login(client, "track_c@example.com")
            headers3 = {"Authorization": f"Bearer {token3}"}
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers3,
            )

            # User 1 checks count
            resp = await client.get("/api/watchlist", headers=headers1)

        assert resp.status_code == 200
        item = resp.json()[0]
        assert item["tracking_count"] == 3
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_tracking_count_zero_not_shown() -> None:
    """A stock not in anyone's watchlist has tracking_count=0 (but this case
    can't occur via API since stock must be in user's watchlist to appear)."""
    # This tests that the field exists and defaults to a reasonable value.
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client, "trackz@example.com")
            headers = {"Authorization": f"Bearer {token}"}
            # Add and then fetch: count should be >= 1
            resp = await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )
        # POST response also includes tracking_count
        assert resp.status_code == 201
        item = resp.json()
        assert item["tracking_count"] >= 1
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_tracking_count_different_stocks() -> None:
    """Each stock has independent tracking_count."""
    _setup()
    try:
        samsung = _get_stock_by_code(TEST_DB_URL, "005930")
        sk = _get_stock_by_code(TEST_DB_URL, "000660")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # User 1: both stocks
            t1 = await _signup_login(client, "td1@example.com")
            h1 = {"Authorization": f"Bearer {t1}"}
            await client.post("/api/watchlist", json={"stock_id": str(samsung.id)}, headers=h1)
            await client.post("/api/watchlist", json={"stock_id": str(sk.id)}, headers=h1)

            # User 2: samsung only
            t2 = await _signup_login(client, "td2@example.com")
            h2 = {"Authorization": f"Bearer {t2}"}
            await client.post("/api/watchlist", json={"stock_id": str(samsung.id)}, headers=h2)

            resp = await client.get("/api/watchlist", headers=h1)

        assert resp.status_code == 200
        data = resp.json()
        counts = {d["stock_code"]: d["tracking_count"] for d in data}
        assert counts["005930"] == 2  # 2 users
        assert counts["000660"] == 1  # 1 user
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_tracking_count_after_remove() -> None:
    """Removing a stock decrements its tracking_count for other users."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # User 1
            t1 = await _signup_login(client, "rm1@example.com")
            h1 = {"Authorization": f"Bearer {t1}"}
            add1 = await client.post("/api/watchlist", json={"stock_id": str(stock.id)}, headers=h1)
            item1_id = add1.json()["id"]

            # User 2
            t2 = await _signup_login(client, "rm2@example.com")
            h2 = {"Authorization": f"Bearer {t2}"}
            await client.post("/api/watchlist", json={"stock_id": str(stock.id)}, headers=h2)

            # Both tracking → count=2
            resp = await client.get("/api/watchlist", headers=h2)
            assert resp.json()[0]["tracking_count"] == 2

            # User 1 removes
            await client.delete(f"/api/watchlist/{item1_id}", headers=h1)

            # User 2 now sees count=1
            resp = await client.get("/api/watchlist", headers=h2)
            assert resp.json()[0]["tracking_count"] == 1
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_tracking_count_in_patch_response() -> None:
    """PATCH /api/watchlist/{id} also returns tracking_count."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client, "patchtrack@example.com")
            headers = {"Authorization": f"Bearer {token}"}
            add_resp = await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )
            item_id = add_resp.json()["id"]

            resp = await client.patch(
                f"/api/watchlist/{item_id}",
                json={"threshold": 5.0},
                headers=headers,
            )

        assert resp.status_code == 200
        assert resp.json()["tracking_count"] == 1
    finally:
        _teardown()
