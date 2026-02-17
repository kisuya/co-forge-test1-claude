from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import raise_error
from app.db.database import get_session_factory
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str


class SignupResponse(BaseModel):
    id: str
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


def get_db() -> Session:  # type: ignore[misc]
    """Yield a database session."""
    settings = get_settings()
    factory = get_session_factory(settings.database_url)
    session = factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        password.encode("utf-8"), password_hash.encode("utf-8")
    )


def create_access_token(user_id: str, secret: str, hours: int) -> str:
    """Create a JWT access token."""
    payload = {
        "sub": user_id,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=hours),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def create_refresh_token(user_id: str, secret: str) -> str:
    """Create a JWT refresh token (30-day expiry)."""
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@router.post(
    "/signup", status_code=status.HTTP_201_CREATED, response_model=SignupResponse
)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> Any:
    """Register a new user with email and password."""
    existing = db.execute(
        select(User).where(User.email == body.email)
    ).scalar_one_or_none()

    if existing is not None:
        raise_error(409, "Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return SignupResponse(id=str(user.id), email=user.email)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> Any:
    """Authenticate user and return JWT tokens."""
    user = db.execute(
        select(User).where(User.email == body.email)
    ).scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise_error(401, "Invalid email or password")

    settings = get_settings()
    access_token = create_access_token(
        str(user.id), settings.jwt_secret_key, settings.jwt_expiry_hours
    )
    refresh_token = create_refresh_token(str(user.id), settings.jwt_secret_key)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest) -> Any:
    """Refresh an expired access token using a valid refresh token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            body.refresh_token, settings.jwt_secret_key, algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        raise_error(401, "Refresh token expired")
    except jwt.InvalidTokenError:
        raise_error(401, "Invalid refresh token")

    if payload.get("type") != "refresh":
        raise_error(401, "Invalid token type")

    user_id = payload["sub"]
    access_token = create_access_token(
        user_id, settings.jwt_secret_key, settings.jwt_expiry_hours
    )
    refresh_token = create_refresh_token(user_id, settings.jwt_secret_key)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
