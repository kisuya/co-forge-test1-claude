from __future__ import annotations

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.config import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="oh-my-stock",
        description="AI-powered stock movement analysis service",
        version="0.1.0",
        debug=settings.debug,
    )

    app.include_router(auth_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
