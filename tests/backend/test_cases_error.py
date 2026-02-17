"""Tests for Cases/Reports API error codes (quality-002)."""
from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.user import User
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_cases_error.db"


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
    if _os.path.exists("test_cases_error.db"):
        _os.remove("test_cases_error.db")


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
        json={"email": "casestest@example.com", "password": "pass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "casestest@example.com", "password": "pass123"},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_cases_nonexistent_report_returns_404() -> None:
    """GET /api/cases/{report_id} with non-existent UUID returns 404."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            fake_id = str(uuid.uuid4())
            resp = await client.get(
                f"/api/cases/{fake_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_cases_invalid_uuid_returns_422() -> None:
    """GET /api/cases/{report_id} with invalid UUID format returns 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            resp = await client.get(
                "/api/cases/not-a-valid-uuid",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_cases_negative_id_returns_422() -> None:
    """GET /api/cases/{report_id} with negative number string returns 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            resp = await client.get(
                "/api/cases/-1",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_reports_nonexistent_id_returns_404() -> None:
    """GET /api/reports/{id} with non-existent UUID returns 404."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            fake_id = str(uuid.uuid4())
            resp = await client.get(
                f"/api/reports/{fake_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_reports_invalid_uuid_returns_422() -> None:
    """GET /api/reports/{id} with invalid UUID format returns 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            resp = await client.get(
                "/api/reports/invalid-string-id",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 422
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_reports_numeric_string_returns_422() -> None:
    """GET /api/reports/{id} with plain numeric string returns 422."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            resp = await client.get(
                "/api/reports/12345",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 422
    finally:
        _teardown()
