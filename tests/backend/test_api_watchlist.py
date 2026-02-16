"""Tests for watchlist CRUD API."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_watchlist.db"


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
    if _os.path.exists("test_watchlist.db"):
        _os.remove("test_watchlist.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(client: AsyncClient) -> str:
    """Helper: create user and return access token."""
    await client.post(
        "/api/auth/signup",
        json={"email": "wluser@example.com", "password": "pass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "wluser@example.com", "password": "pass123"},
    )
    return resp.json()["access_token"]


async def _get_stock_id(client: AsyncClient) -> str:
    """Helper: search for a stock and return its ID."""
    resp = await client.get("/api/stocks/search", params={"q": "삼성전자"})
    return resp.json()[0]["id"]


@pytest.mark.asyncio
async def test_watchlist_add_and_get() -> None:
    """Should add a stock and retrieve the watchlist."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            stock_id = await _get_stock_id(client)

            resp = await client.post(
                "/api/watchlist",
                json={"stock_id": stock_id},
                headers=headers,
            )
            assert resp.status_code == 201
            item = resp.json()
            assert item["stock_name"] == "삼성전자"
            assert item["threshold"] == 3.0

            resp = await client.get("/api/watchlist", headers=headers)
            assert resp.status_code == 200
            assert len(resp.json()) == 1
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_watchlist_duplicate_returns_409() -> None:
    """Adding the same stock twice should return 409."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            stock_id = await _get_stock_id(client)

            await client.post(
                "/api/watchlist", json={"stock_id": stock_id}, headers=headers
            )
            resp = await client.post(
                "/api/watchlist", json={"stock_id": stock_id}, headers=headers
            )
            assert resp.status_code == 409
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_watchlist_delete() -> None:
    """Should remove a stock from the watchlist."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            stock_id = await _get_stock_id(client)

            add_resp = await client.post(
                "/api/watchlist", json={"stock_id": stock_id}, headers=headers
            )
            item_id = add_resp.json()["id"]

            resp = await client.delete(f"/api/watchlist/{item_id}", headers=headers)
            assert resp.status_code == 204

            resp = await client.get("/api/watchlist", headers=headers)
            assert len(resp.json()) == 0
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_watchlist_patch_threshold() -> None:
    """Should update the threshold for a watchlist item."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            stock_id = await _get_stock_id(client)

            add_resp = await client.post(
                "/api/watchlist", json={"stock_id": stock_id}, headers=headers
            )
            item_id = add_resp.json()["id"]

            resp = await client.patch(
                f"/api/watchlist/{item_id}",
                json={"threshold": 5.0},
                headers=headers,
            )
            assert resp.status_code == 200
            assert resp.json()["threshold"] == 5.0
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_watchlist_requires_auth() -> None:
    """Accessing watchlist without auth should return 401/403."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/watchlist")
        assert resp.status_code in (401, 403)
    finally:
        _teardown()
