"""Tests for Discussion CRUD API (community-002)."""
from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.stock import Stock
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_discussion_api.db"


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
    if _os.path.exists("test_discussion_api.db"):
        _os.remove("test_discussion_api.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(client: AsyncClient, email: str = "disc@example.com") -> str:
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


# --- Create discussion ---

@pytest.mark.asyncio
async def test_create_discussion() -> None:
    """POST /api/stocks/{stock_id}/discussions creates a discussion."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": "삼성전자 실적 발표가 기대됩니다"},
                headers=headers,
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["content"] == "삼성전자 실적 발표가 기대됩니다"
        assert data["author_name"] == "disc"  # email prefix
        assert data["comment_count"] == 0
        assert data["is_mine"] is True
        assert "id" in data
        assert "created_at" in data
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_create_discussion_with_nickname() -> None:
    """Author name uses nickname when set."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # Set nickname
            await client.put(
                "/api/profile",
                json={"nickname": "투자왕"},
                headers=headers,
            )

            resp = await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": "테스트 내용"},
                headers=headers,
            )

        assert resp.status_code == 201
        assert resp.json()["author_name"] == "투자왕"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_create_discussion_empty_content_422() -> None:
    """Empty content returns 422."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": ""},
                headers=headers,
            )

        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_create_discussion_too_long_422() -> None:
    """Content over 2000 chars returns 422."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": "x" * 2001},
                headers=headers,
            )

        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_create_discussion_boundary_2000() -> None:
    """Content at exactly 2000 chars succeeds."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": "x" * 2000},
                headers=headers,
            )

        assert resp.status_code == 201
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_create_discussion_boundary_1() -> None:
    """Content at exactly 1 char succeeds."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": "x"},
                headers=headers,
            )

        assert resp.status_code == 201
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_create_discussion_html_stripped() -> None:
    """HTML tags are stripped from content."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": "<script>alert('xss')</script>실적 좋다"},
                headers=headers,
            )

        assert resp.status_code == 201
        assert "<script>" not in resp.json()["content"]
        assert "실적 좋다" in resp.json()["content"]
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_create_discussion_nonexistent_stock_404() -> None:
    """Discussion for nonexistent stock returns 404."""
    _setup()
    try:
        fake_id = str(uuid.uuid4())
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.post(
                f"/api/stocks/{fake_id}/discussions",
                json={"content": "테스트"},
                headers=headers,
            )

        assert resp.status_code == 404
    finally:
        _teardown()


# --- List discussions ---

@pytest.mark.asyncio
async def test_list_discussions() -> None:
    """GET /api/stocks/{stock_id}/discussions returns list."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # Create 3 discussions
            for i in range(3):
                await client.post(
                    f"/api/stocks/{stock.id}/discussions",
                    json={"content": f"토론 {i}"},
                    headers=headers,
                )

            resp = await client.get(
                f"/api/stocks/{stock.id}/discussions",
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["discussions"]) == 3
        assert data["pagination"]["total"] == 3
        assert data["pagination"]["has_more"] is False
        # Newest first
        assert "토론 2" in data["discussions"][0]["content"]
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_list_discussions_pagination() -> None:
    """Pagination works with 21 discussions (2 pages at per_page=20)."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            for i in range(21):
                await client.post(
                    f"/api/stocks/{stock.id}/discussions",
                    json={"content": f"토론 {i:02d}"},
                    headers=headers,
                )

            # Page 1
            resp1 = await client.get(
                f"/api/stocks/{stock.id}/discussions?page=1&per_page=20",
                headers=headers,
            )
            # Page 2
            resp2 = await client.get(
                f"/api/stocks/{stock.id}/discussions?page=2&per_page=20",
                headers=headers,
            )

        data1 = resp1.json()
        assert len(data1["discussions"]) == 20
        assert data1["pagination"]["total"] == 21
        assert data1["pagination"]["has_more"] is True

        data2 = resp2.json()
        assert len(data2["discussions"]) == 1
        assert data2["pagination"]["has_more"] is False
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_list_discussions_is_mine() -> None:
    """is_mine is True for own discussions, False for others'."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # User 1 creates a discussion
            token1 = await _signup_login(client, "user1@example.com")
            headers1 = {"Authorization": f"Bearer {token1}"}
            await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": "User1의 글"},
                headers=headers1,
            )

            # User 2 views
            token2 = await _signup_login(client, "user2@example.com")
            headers2 = {"Authorization": f"Bearer {token2}"}

            resp = await client.get(
                f"/api/stocks/{stock.id}/discussions",
                headers=headers2,
            )

        data = resp.json()
        assert len(data["discussions"]) == 1
        assert data["discussions"][0]["is_mine"] is False
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_list_discussions_comment_count() -> None:
    """comment_count in discussion list response is accurate."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # Create discussion
            resp = await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": "댓글 테스트"},
                headers=headers,
            )
            disc_id = resp.json()["id"]

            # Add 3 comments
            for i in range(3):
                await client.post(
                    f"/api/discussions/{disc_id}/comments",
                    json={"content": f"댓글 {i}"},
                    headers=headers,
                )

            # List discussions
            resp = await client.get(
                f"/api/stocks/{stock.id}/discussions",
                headers=headers,
            )

        data = resp.json()
        assert data["discussions"][0]["comment_count"] == 3
    finally:
        _teardown()


# --- Update discussion ---

@pytest.mark.asyncio
async def test_update_discussion() -> None:
    """PUT /api/discussions/{id} updates the discussion."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            create_resp = await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": "원본 내용"},
                headers=headers,
            )
            disc_id = create_resp.json()["id"]

            resp = await client.put(
                f"/api/discussions/{disc_id}",
                json={"content": "수정된 내용"},
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "수정된 내용"
        assert data["is_mine"] is True
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_update_discussion_403_not_owner() -> None:
    """Cannot update another user's discussion."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # User 1 creates
            token1 = await _signup_login(client, "owner@example.com")
            headers1 = {"Authorization": f"Bearer {token1}"}
            create_resp = await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": "원본"},
                headers=headers1,
            )
            disc_id = create_resp.json()["id"]

            # User 2 tries to update
            token2 = await _signup_login(client, "other@example.com")
            headers2 = {"Authorization": f"Bearer {token2}"}
            resp = await client.put(
                f"/api/discussions/{disc_id}",
                json={"content": "해킹 시도"},
                headers=headers2,
            )

        assert resp.status_code == 403
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_update_discussion_404() -> None:
    """Update nonexistent discussion returns 404."""
    _setup()
    try:
        fake_id = str(uuid.uuid4())
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.put(
                f"/api/discussions/{fake_id}",
                json={"content": "수정"},
                headers=headers,
            )

        assert resp.status_code == 404
    finally:
        _teardown()


# --- Delete discussion ---

@pytest.mark.asyncio
async def test_delete_discussion() -> None:
    """DELETE /api/discussions/{id} deletes the discussion."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            create_resp = await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": "삭제할 글"},
                headers=headers,
            )
            disc_id = create_resp.json()["id"]

            resp = await client.delete(
                f"/api/discussions/{disc_id}",
                headers=headers,
            )

        assert resp.status_code == 204
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_delete_discussion_cascades_comments() -> None:
    """Deleting a discussion also deletes its comments."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            create_resp = await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": "댓글 있는 글"},
                headers=headers,
            )
            disc_id = create_resp.json()["id"]

            # Add comments
            await client.post(
                f"/api/discussions/{disc_id}/comments",
                json={"content": "댓글1"},
                headers=headers,
            )
            await client.post(
                f"/api/discussions/{disc_id}/comments",
                json={"content": "댓글2"},
                headers=headers,
            )

            # Delete discussion
            del_resp = await client.delete(
                f"/api/discussions/{disc_id}",
                headers=headers,
            )

            # Verify comments are gone
            comment_resp = await client.get(
                f"/api/discussions/{disc_id}/comments",
                headers=headers,
            )

        assert del_resp.status_code == 204
        assert comment_resp.status_code == 404  # discussion not found
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_delete_discussion_403_not_owner() -> None:
    """Cannot delete another user's discussion."""
    _setup()
    try:
        stock = _get_stock_by_code()
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token1 = await _signup_login(client, "owner2@example.com")
            headers1 = {"Authorization": f"Bearer {token1}"}
            create_resp = await client.post(
                f"/api/stocks/{stock.id}/discussions",
                json={"content": "내 글"},
                headers=headers1,
            )
            disc_id = create_resp.json()["id"]

            token2 = await _signup_login(client, "other2@example.com")
            headers2 = {"Authorization": f"Bearer {token2}"}
            resp = await client.delete(
                f"/api/discussions/{disc_id}",
                headers=headers2,
            )

        assert resp.status_code == 403
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_delete_discussion_404() -> None:
    """Delete nonexistent discussion returns 404."""
    _setup()
    try:
        fake_id = str(uuid.uuid4())
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.delete(
                f"/api/discussions/{fake_id}",
                headers=headers,
            )

        assert resp.status_code == 404
    finally:
        _teardown()
