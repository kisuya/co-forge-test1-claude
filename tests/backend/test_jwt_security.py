"""Tests for JWT security hardening."""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory

TEST_DB_URL = "sqlite:///test_jwt_security.db"
SAFE_KEY = os.environ["JWT_SECRET_KEY"]


def _get_test_db() -> Session:  # type: ignore[misc]
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()


def _setup() -> None:
    create_tables(TEST_DB_URL)


def _teardown() -> None:
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_jwt_security.db"):
        os.remove("test_jwt_security.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


# --- JWT_SECRET_KEY validation ---


def test_jwt_key_minimum_32_bytes() -> None:
    """JWT_SECRET_KEY in test env must be at least 32 bytes."""
    assert len(SAFE_KEY.encode("utf-8")) >= 32


def test_missing_jwt_key_raises_valueerror() -> None:
    """Settings should raise ValueError when JWT_SECRET_KEY is empty."""
    original = os.environ.get("JWT_SECRET_KEY")
    try:
        os.environ["JWT_SECRET_KEY"] = ""
        from app.config import Settings
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            Settings()
    finally:
        if original is not None:
            os.environ["JWT_SECRET_KEY"] = original


def test_short_jwt_key_raises_valueerror() -> None:
    """Settings should raise ValueError when JWT_SECRET_KEY is too short."""
    original = os.environ.get("JWT_SECRET_KEY")
    try:
        os.environ["JWT_SECRET_KEY"] = "short-key"
        from app.config import Settings
        with pytest.raises(ValueError, match="at least 32 bytes"):
            Settings()
    finally:
        if original is not None:
            os.environ["JWT_SECRET_KEY"] = original


def test_valid_jwt_key_accepted() -> None:
    """Settings should accept a key of 32+ bytes."""
    from app.config import Settings
    settings = Settings()
    assert len(settings.jwt_secret_key.encode("utf-8")) >= 32


# --- No InsecureKeyLengthWarning ---


def test_no_insecure_key_warning() -> None:
    """JWT operations should not produce InsecureKeyLengthWarning."""
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        token = jwt.encode(
            {"sub": "test", "type": "access", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            SAFE_KEY,
            algorithm="HS256",
        )
        jwt.decode(token, SAFE_KEY, algorithms=["HS256"])
        insecure_warnings = [
            x for x in w if "InsecureKeyLength" in str(x.category.__name__)
        ]
        assert len(insecure_warnings) == 0, f"Got {len(insecure_warnings)} InsecureKeyLengthWarning(s)"


# --- Token expired response format ---


@pytest.mark.asyncio
async def test_expired_token_returns_token_expired_code() -> None:
    """Expired token should return 401 with code=TOKEN_EXPIRED."""
    _setup()
    try:
        expired_token = jwt.encode(
            {
                "sub": "00000000-0000-0000-0000-000000000001",
                "type": "access",
                "exp": datetime.now(timezone.utc) - timedelta(seconds=10),
                "iat": datetime.now(timezone.utc) - timedelta(hours=1),
            },
            SAFE_KEY,
            algorithm="HS256",
        )
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/me",
                headers={"Authorization": f"Bearer {expired_token}"},
            )
        assert resp.status_code == 401
        data = resp.json()
        detail = data.get("detail", {})
        assert detail.get("code") == "TOKEN_EXPIRED"
        assert "Token expired" in detail.get("detail", "")
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_valid_token_works_with_secure_key() -> None:
    """A valid token signed with the secure key should authenticate."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/signup",
                json={"email": "secure@example.com", "password": "pass123"},
            )
            login_resp = await client.post(
                "/api/auth/login",
                json={"email": "secure@example.com", "password": "pass123"},
            )
            token = login_resp.json()["access_token"]
            resp = await client.get(
                "/api/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        assert resp.json()["email"] == "secure@example.com"
    finally:
        _teardown()
