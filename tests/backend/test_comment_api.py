"""Tests for Discussion Comment API (community-003)."""
from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.stock import Stock
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_comment_api.db"


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
    if _os.path.exists("test_comment_api.db"):
        _os.remove("test_comment_api.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(client: AsyncClient, email: str = "comment@example.com") -> str:
    await client.post(
        "/api/auth/signup",
        json={"email": email, "password": "pass1234"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "pass1234"},
    )
    return resp.json()["access_token"]


def _get_stock_by_code(code: str = "005930") -> Stock:
    from sqlalchemy import select
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    stock = session.execute(
        select(Stock).where(Stock.code == code)
    ).scalar_one()
    session.close()
    return stock


async def _create_discussion(client: AsyncClient, stock_id: str, headers: dict) -> str:
    """Helper to create a discussion and return its ID."""
    resp = await client.post(
        f"/api/stocks/{stock_id}/discussions",
        json={"content": "테스트 토론 글"},
        headers=headers,
    )
    return resp.json()["id"]


# --- Create comment ---

@pytest.mark.asyncio
async def test_create_comment() -> None:
    """POST /api/discussions/{id}/comments creates a comment."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            disc_id = await _create_discussion(client, str(stock.id), headers)

            resp = await client.post(
                f"/api/discussions/{disc_id}/comments",
                json={"content": "좋은 의견입니다"},
                headers=headers,
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["content"] == "좋은 의견입니다"
        assert data["author_name"] == "comment"  # email prefix
        assert data["is_mine"] is True
        assert "id" in data
        assert "created_at" in data
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_list_comments_asc_order() -> None:
    """GET /api/discussions/{id}/comments returns comments in ASC order."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            disc_id = await _create_discussion(client, str(stock.id), headers)

            for i in range(3):
                await client.post(
                    f"/api/discussions/{disc_id}/comments",
                    json={"content": f"댓글 {i}"},
                    headers=headers,
                )

            resp = await client.get(
                f"/api/discussions/{disc_id}/comments",
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        # ASC order (oldest first)
        assert "댓글 0" in data[0]["content"]
        assert "댓글 2" in data[2]["content"]
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_comment_is_mine_false_for_others() -> None:
    """is_mine is False when viewing another user's comment."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # User 1 creates discussion and comment
            token1 = await _signup_login(client, "commenter1@example.com")
            headers1 = {"Authorization": f"Bearer {token1}"}
            disc_id = await _create_discussion(client, str(stock.id), headers1)
            await client.post(
                f"/api/discussions/{disc_id}/comments",
                json={"content": "User1 댓글"},
                headers=headers1,
            )

            # User 2 views
            token2 = await _signup_login(client, "viewer@example.com")
            headers2 = {"Authorization": f"Bearer {token2}"}
            resp = await client.get(
                f"/api/discussions/{disc_id}/comments",
                headers=headers2,
            )

        data = resp.json()
        assert len(data) == 1
        assert data[0]["is_mine"] is False
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_delete_comment() -> None:
    """DELETE /api/comments/{id} deletes own comment."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            disc_id = await _create_discussion(client, str(stock.id), headers)
            create_resp = await client.post(
                f"/api/discussions/{disc_id}/comments",
                json={"content": "삭제할 댓글"},
                headers=headers,
            )
            comment_id = create_resp.json()["id"]

            del_resp = await client.delete(
                f"/api/comments/{comment_id}",
                headers=headers,
            )

            # Verify deletion
            list_resp = await client.get(
                f"/api/discussions/{disc_id}/comments",
                headers=headers,
            )

        assert del_resp.status_code == 204
        assert len(list_resp.json()) == 0
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_delete_comment_403_not_owner() -> None:
    """Cannot delete another user's comment."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # User 1 creates discussion and comment
            token1 = await _signup_login(client, "author@example.com")
            headers1 = {"Authorization": f"Bearer {token1}"}
            disc_id = await _create_discussion(client, str(stock.id), headers1)
            create_resp = await client.post(
                f"/api/discussions/{disc_id}/comments",
                json={"content": "내 댓글"},
                headers=headers1,
            )
            comment_id = create_resp.json()["id"]

            # User 2 tries to delete
            token2 = await _signup_login(client, "attacker@example.com")
            headers2 = {"Authorization": f"Bearer {token2}"}
            resp = await client.delete(
                f"/api/comments/{comment_id}",
                headers=headers2,
            )

        assert resp.status_code == 403
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_delete_comment_404() -> None:
    """Delete nonexistent comment returns 404."""
    _setup()
    try:
        fake_id = str(uuid.uuid4())
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.delete(
                f"/api/comments/{fake_id}",
                headers=headers,
            )

        assert resp.status_code == 404
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_comment_100_limit() -> None:
    """Discussion allows max 100 comments; 101st returns 400."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            disc_id = await _create_discussion(client, str(stock.id), headers)

            # Reset rate limiter to avoid 429 during bulk insert
            from app.core.rate_limit import counter
            counter.reset()

            # Create 100 comments
            for i in range(100):
                if i % 50 == 0 and i > 0:
                    counter.reset()
                r = await client.post(
                    f"/api/discussions/{disc_id}/comments",
                    json={"content": f"댓글 {i}"},
                    headers=headers,
                )
                assert r.status_code == 201, f"Comment {i} failed: {r.status_code}"

            counter.reset()

            # 101st should fail
            resp = await client.post(
                f"/api/discussions/{disc_id}/comments",
                json={"content": "초과 댓글"},
                headers=headers,
            )

        assert resp.status_code == 400
        assert "Maximum comment limit" in resp.json().get("message", resp.json().get("detail", ""))
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_comment_empty_content_422() -> None:
    """Empty comment content returns 422."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            disc_id = await _create_discussion(client, str(stock.id), headers)

            resp = await client.post(
                f"/api/discussions/{disc_id}/comments",
                json={"content": ""},
                headers=headers,
            )

        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_comment_too_long_422() -> None:
    """Comment over 500 chars returns 422."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            disc_id = await _create_discussion(client, str(stock.id), headers)

            resp = await client.post(
                f"/api/discussions/{disc_id}/comments",
                json={"content": "x" * 501},
                headers=headers,
            )

        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_comment_boundary_500() -> None:
    """Comment at exactly 500 chars succeeds."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            disc_id = await _create_discussion(client, str(stock.id), headers)

            resp = await client.post(
                f"/api/discussions/{disc_id}/comments",
                json={"content": "x" * 500},
                headers=headers,
            )

        assert resp.status_code == 201
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_comment_boundary_1() -> None:
    """Comment at exactly 1 char succeeds."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            disc_id = await _create_discussion(client, str(stock.id), headers)

            resp = await client.post(
                f"/api/discussions/{disc_id}/comments",
                json={"content": "x"},
                headers=headers,
            )

        assert resp.status_code == 201
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_comment_nonexistent_discussion_404() -> None:
    """Comment on nonexistent discussion returns 404."""
    _setup()
    try:
        fake_id = str(uuid.uuid4())
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.post(
                f"/api/discussions/{fake_id}/comments",
                json={"content": "댓글"},
                headers=headers,
            )

        assert resp.status_code == 404
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_list_comments_nonexistent_discussion_404() -> None:
    """List comments for nonexistent discussion returns 404."""
    _setup()
    try:
        fake_id = str(uuid.uuid4())
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.get(
                f"/api/discussions/{fake_id}/comments",
                headers=headers,
            )

        assert resp.status_code == 404
    finally:
        _teardown()
