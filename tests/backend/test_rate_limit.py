"""Tests for API rate limiting middleware (quality-006)."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.core.rate_limit import counter
from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_rate_limit.db"


def _get_test_db() -> Session:  # type: ignore[misc]
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()


def _setup() -> None:
    counter.reset()
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    seed_stocks(session)
    session.close()


def _teardown() -> None:
    counter.reset()
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os
    if os.path.exists("test_rate_limit.db"):
        os.remove("test_rate_limit.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


@pytest.mark.asyncio
async def test_login_within_limit_returns_normal_response() -> None:
    """Login attempts within rate limit should work normally."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/signup",
                json={"email": "ratelimit@example.com", "password": "pass123"},
            )
            resp = await client.post(
                "/api/auth/login",
                json={"email": "ratelimit@example.com", "password": "pass123"},
            )
        assert resp.status_code == 200
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_login_exceeds_rate_limit_returns_429() -> None:
    """Exceeding login rate limit should return 429 with Retry-After."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/signup",
                json={"email": "ratelimit2@example.com", "password": "pass123"},
            )
            responses = []
            for _ in range(6):
                resp = await client.post(
                    "/api/auth/login",
                    json={"email": "ratelimit2@example.com", "password": "pass123"},
                )
                responses.append(resp)

        # The 6th request should be rate limited
        assert responses[-1].status_code == 429
        assert "retry-after" in responses[-1].headers
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_rate_limit_429_standard_error_format() -> None:
    """429 responses should use standard error format."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/signup",
                json={"email": "ratelimit4@example.com", "password": "pass123"},
            )
            resp = None
            for _ in range(6):
                resp = await client.post(
                    "/api/auth/login",
                    json={"email": "ratelimit4@example.com", "password": "pass123"},
                )
                if resp.status_code == 429:
                    break

        assert resp is not None
        assert resp.status_code == 429
        data = resp.json()
        assert data["error"] == "TooManyRequests"
        assert data["status_code"] == 429
        assert "message" in data
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_different_endpoints_have_separate_limits() -> None:
    """Health endpoint should not be affected by login rate limiting."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/signup",
                json={"email": "ratelimit5@example.com", "password": "pass123"},
            )
            for _ in range(6):
                await client.post(
                    "/api/auth/login",
                    json={"email": "ratelimit5@example.com", "password": "pass123"},
                )

            # Health endpoint should still work
            resp = await client.get("/health")
        assert resp.status_code == 200
    finally:
        _teardown()
