from __future__ import annotations

import os
from dataclasses import dataclass, field


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
    jwt_secret_key: str = field(
        default_factory=lambda: os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    )
    jwt_expiry_hours: int = field(
        default_factory=lambda: int(os.getenv("JWT_EXPIRY_HOURS", "168"))
    )
    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    dart_api_key: str = field(
        default_factory=lambda: os.getenv("DART_API_KEY", "")
    )
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true"
    )


def get_settings() -> Settings:
    """Return a new Settings instance from current env."""
    return Settings()
