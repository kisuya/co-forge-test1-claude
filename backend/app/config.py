from __future__ import annotations

import os
from dataclasses import dataclass, field

MIN_JWT_KEY_BYTES = 32


def _load_jwt_secret() -> str:
    """Load and validate JWT_SECRET_KEY from environment."""
    key = os.getenv("JWT_SECRET_KEY", "")
    if not key:
        raise ValueError(
            "JWT_SECRET_KEY environment variable is not set. "
            "Please set a secure key of at least 32 bytes. "
            "Example: export JWT_SECRET_KEY=$(python -c "
            "'import secrets; print(secrets.token_hex(32))')"
        )
    if len(key.encode("utf-8")) < MIN_JWT_KEY_BYTES:
        raise ValueError(
            f"JWT_SECRET_KEY must be at least {MIN_JWT_KEY_BYTES} bytes. "
            f"Current key is {len(key.encode('utf-8'))} bytes. "
            "Generate a secure key: python -c "
            "'import secrets; print(secrets.token_hex(32))'"
        )
    return key


@dataclass(frozen=True)
class Settings:
    """Application configuration loaded from environment variables."""

    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://user:pass@localhost:5432/ohmystock",
        )
    )
    redis_url: str = field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    jwt_secret_key: str = field(default_factory=_load_jwt_secret)
    jwt_expiry_hours: int = field(
        default_factory=lambda: int(os.getenv("JWT_EXPIRY_HOURS", "168"))
    )
    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    dart_api_key: str = field(
        default_factory=lambda: os.getenv("DART_API_KEY", "")
    )
    news_api_key: str = field(
        default_factory=lambda: os.getenv("NEWS_API_KEY", "")
    )
    naver_client_id: str = field(
        default_factory=lambda: os.getenv("NAVER_CLIENT_ID", "")
    )
    naver_client_secret: str = field(
        default_factory=lambda: os.getenv("NAVER_CLIENT_SECRET", "")
    )
    vapid_public_key: str = field(
        default_factory=lambda: os.getenv("VAPID_PUBLIC_KEY", "")
    )
    vapid_private_key: str = field(
        default_factory=lambda: os.getenv("VAPID_PRIVATE_KEY", "")
    )
    vapid_contact: str = field(
        default_factory=lambda: os.getenv("VAPID_CONTACT", "mailto:admin@ohmystock.kr")
    )
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true"
    )


def get_settings() -> Settings:
    """Return a new Settings instance from current env."""
    return Settings()
