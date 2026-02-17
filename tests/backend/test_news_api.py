"""Tests for news feed API (news-003)."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.news_article import NewsArticle
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_news_api.db"


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
    if os.path.exists("test_news_api.db"):
        os.remove("test_news_api.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(client: AsyncClient, email: str = "news@example.com") -> str:
    await client.post(
        "/api/auth/signup",
        json={"email": email, "password": "pass1234"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "pass1234"},
    )
    return resp.json()["access_token"]


def _get_kr_stock() -> Stock:
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    stock = session.execute(
        select(Stock).where(Stock.market == "KRX")
    ).scalars().first()
    session.close()
    return stock


def _get_us_stock() -> Stock:
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    stock = session.execute(
        select(Stock).where(Stock.market.in_(("NYSE", "NASDAQ")))
    ).scalars().first()
    session.close()
    return stock


def _seed_news(stock_id, count=5, importance="medium") -> None:
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    now = datetime.now(timezone.utc)
    for i in range(count):
        article = NewsArticle(
            stock_id=stock_id,
            title=f"테스트 뉴스 {i+1}",
            url=f"https://example.com/news/{stock_id}/{uuid.uuid4()}",
            source="TestSource",
            published_at=now - timedelta(hours=i),
            content_summary=f"요약 {i+1}",
            importance=importance,
        )
        session.add(article)
    session.commit()
    session.close()


async def _add_to_watchlist(client: AsyncClient, stock_id: str, headers: dict) -> None:
    await client.post(
        "/api/watchlist",
        json={"stock_id": stock_id},
        headers=headers,
    )


# ── API tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_news_feed_full() -> None:
    """GET /api/news returns news for user's watchlist stocks."""
    _setup()
    try:
        app = _make_app()
        stock = _get_kr_stock()
        _seed_news(stock.id, count=3, importance="high")
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            await _add_to_watchlist(client, str(stock.id), headers)

            resp = await client.get("/api/news", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 3
            assert len(data["items"]) == 3
            assert data["page"] == 1
            assert data["per_page"] == 20

            # Check item fields
            item = data["items"][0]
            assert "id" in item
            assert item["stock_id"] == str(stock.id)
            assert item["stock_name"] is not None
            assert "title" in item
            assert "url" in item
            assert "source" in item
            assert item["importance"] == "high"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_news_feed_stock_filter() -> None:
    """GET /api/news?stock_id=X filters by specific stock."""
    _setup()
    try:
        app = _make_app()
        stock_kr = _get_kr_stock()
        stock_us = _get_us_stock()

        if stock_us is None:
            pytest.skip("No US stocks seeded")

        _seed_news(stock_kr.id, count=3)
        _seed_news(stock_us.id, count=2)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            await _add_to_watchlist(client, str(stock_kr.id), headers)
            await _add_to_watchlist(client, str(stock_us.id), headers)

            # Filter by KR stock
            resp = await client.get(
                f"/api/news?stock_id={stock_kr.id}", headers=headers
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 3
            for item in data["items"]:
                assert item["stock_id"] == str(stock_kr.id)
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_news_feed_importance_filter() -> None:
    """GET /api/news?importance=high filters by importance."""
    _setup()
    try:
        app = _make_app()
        stock = _get_kr_stock()
        _seed_news(stock.id, count=3, importance="high")
        _seed_news(stock.id, count=2, importance="low")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            await _add_to_watchlist(client, str(stock.id), headers)

            resp = await client.get("/api/news?importance=high", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 3
            for item in data["items"]:
                assert item["importance"] == "high"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_news_feed_pagination() -> None:
    """GET /api/news with pagination returns correct page."""
    _setup()
    try:
        app = _make_app()
        stock = _get_kr_stock()
        _seed_news(stock.id, count=25)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            await _add_to_watchlist(client, str(stock.id), headers)

            # Page 1
            resp = await client.get("/api/news?page=1&per_page=10", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 25
            assert len(data["items"]) == 10
            assert data["has_more"] is True

            # Page 3
            resp = await client.get("/api/news?page=3&per_page=10", headers=headers)
            data = resp.json()
            assert len(data["items"]) == 5
            assert data["has_more"] is False
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_news_feed_empty_watchlist() -> None:
    """GET /api/news with empty watchlist returns empty list with message."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.get("/api/news", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["items"] == []
            assert data["total"] == 0
            assert data["message"] == "뉴스가 없습니다"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_news_feed_no_news() -> None:
    """GET /api/news returns empty when watchlist has stocks but no news."""
    _setup()
    try:
        app = _make_app()
        stock = _get_kr_stock()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            await _add_to_watchlist(client, str(stock.id), headers)

            resp = await client.get("/api/news", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["items"] == []
            assert data["total"] == 0
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_news_feed_unauthorized() -> None:
    """GET /api/news without token returns 401/403."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/news")
            assert resp.status_code in (401, 403)
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_news_feed_invalid_importance() -> None:
    """GET /api/news with invalid importance returns 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.get("/api/news?importance=invalid", headers=headers)
            assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_news_feed_ordered_by_published_at() -> None:
    """GET /api/news returns articles ordered by published_at DESC."""
    _setup()
    try:
        app = _make_app()
        stock = _get_kr_stock()
        _seed_news(stock.id, count=5)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            await _add_to_watchlist(client, str(stock.id), headers)

            resp = await client.get("/api/news", headers=headers)
            assert resp.status_code == 200
            items = resp.json()["items"]
            # Most recent first
            for i in range(len(items) - 1):
                if items[i]["published_at"] and items[i + 1]["published_at"]:
                    assert items[i]["published_at"] >= items[i + 1]["published_at"]
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_news_feed_per_page_max_50() -> None:
    """GET /api/news per_page maximum is 50."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.get("/api/news?per_page=100", headers=headers)
            assert resp.status_code == 422
    finally:
        _teardown()
