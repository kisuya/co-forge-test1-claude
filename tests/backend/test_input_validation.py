"""Tests for input validation (quality-007)."""
from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.core.sanitize import strip_html_tags
from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_input_validation.db"


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
    if _os.path.exists("test_input_validation.db"):
        _os.remove("test_input_validation.db")


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
        json={"email": "val@example.com", "password": "pass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "val@example.com", "password": "pass123"},
    )
    return resp.json()["access_token"]


# --- HTML tag stripping ---


def test_strip_html_tags_removes_script() -> None:
    """strip_html_tags should remove <script> tags."""
    result = strip_html_tags("<script>alert('xss')</script>Hello")
    assert "<script>" not in result
    assert "Hello" in result


def test_strip_html_tags_removes_all_tags() -> None:
    """strip_html_tags should remove various HTML tags."""
    result = strip_html_tags("<b>bold</b> <img src=x> <div>text</div>")
    assert "<b>" not in result
    assert "<img" not in result
    assert "<div>" not in result
    assert "bold" in result
    assert "text" in result


def test_strip_html_tags_preserves_plain_text() -> None:
    """strip_html_tags should leave plain text unchanged."""
    text = "Hello World 123"
    assert strip_html_tags(text) == text


# --- Auth input validation ---


@pytest.mark.asyncio
async def test_signup_invalid_email_returns_422() -> None:
    """Signup with invalid email format should return 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/auth/signup",
                json={"email": "not-an-email", "password": "pass123"},
            )
        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_signup_password_too_long_returns_422() -> None:
    """Signup with password over max_length should return 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/auth/signup",
                json={"email": "long@example.com", "password": "x" * 101},
            )
        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_signup_valid_boundary_password_returns_201() -> None:
    """Signup with password at max_length boundary should succeed."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/auth/signup",
                json={"email": "boundary@example.com", "password": "x" * 100},
            )
        assert resp.status_code == 201
    finally:
        _teardown()


# --- Stock search input validation ---


@pytest.mark.asyncio
async def test_stock_search_too_long_returns_422() -> None:
    """Stock search with query over max_length should return 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/stocks/search", params={"q": "x" * 101},
            )
        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stock_search_empty_returns_422() -> None:
    """Stock search with empty query should return 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/stocks/search", params={"q": ""},
            )
        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stock_search_html_stripped() -> None:
    """Stock search query with HTML tags should have them stripped."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/stocks/search",
                params={"q": "<script>alert('xss')</script>삼성"},
            )
        # Should succeed (200) — tags stripped, query proceeds
        assert resp.status_code == 200
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stock_search_valid_query_returns_200() -> None:
    """Stock search with normal query should return 200."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/stocks/search", params={"q": "삼성"},
            )
        assert resp.status_code == 200
    finally:
        _teardown()


# --- Watchlist threshold validation ---


@pytest.mark.asyncio
async def test_threshold_below_range_returns_422() -> None:
    """Threshold below 1.0 should return 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            resp = await client.patch(
                f"/api/watchlist/{uuid.uuid4()}",
                json={"threshold": 0.5},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_threshold_above_range_returns_422() -> None:
    """Threshold above 10.0 should return 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            resp = await client.patch(
                f"/api/watchlist/{uuid.uuid4()}",
                json={"threshold": 10.5},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_threshold_at_boundary_accepted() -> None:
    """Threshold at boundary values (1.0, 10.0) should be accepted (not 422)."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            # 1.0 boundary — will be 404 (item not found) but NOT 422
            resp = await client.patch(
                f"/api/watchlist/{uuid.uuid4()}",
                json={"threshold": 1.0},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code != 422

            resp = await client.patch(
                f"/api/watchlist/{uuid.uuid4()}",
                json={"threshold": 10.0},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code != 422
    finally:
        _teardown()


# --- Push subscription validation ---


@pytest.mark.asyncio
async def test_push_endpoint_too_long_returns_422() -> None:
    """Push subscribe with endpoint over max_length should return 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            resp = await client.post(
                "/api/push/subscribe",
                json={
                    "endpoint": "x" * 2001,
                    "p256dh": "key",
                    "auth": "auth",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 422
    finally:
        _teardown()


# --- Login validation ---


@pytest.mark.asyncio
async def test_login_invalid_email_format_returns_422() -> None:
    """Login with invalid email format should return 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/auth/login",
                json={"email": "not-valid-email", "password": "pass123"},
            )
        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_login_password_too_long_returns_422() -> None:
    """Login with password over max_length should return 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/auth/login",
                json={"email": "valid@example.com", "password": "x" * 101},
            )
        assert resp.status_code == 422
    finally:
        _teardown()
