from __future__ import annotations

from typing import Any

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_session_factory
from app.config import get_settings
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str


class SignupResponse(BaseModel):
    id: str
    email: str


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


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=SignupResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> Any:
    """Register a new user with email and password."""
    existing = db.execute(
        select(User).where(User.email == body.email)
    ).scalar_one_or_none()

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return SignupResponse(id=str(user.id), email=user.email)
