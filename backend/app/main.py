from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.deps import get_current_user
from app.api.reports import router as reports_router
from app.api.stocks import router as stocks_router
from app.api.watchlist import router as watchlist_router
from app.config import get_settings
from app.models.user import User


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="oh-my-stock",
        description="AI-powered stock movement analysis service",
        version="0.1.0",
        debug=settings.debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(stocks_router)
    app.include_router(watchlist_router)
    app.include_router(reports_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/me")
    def me(user: User = Depends(get_current_user)) -> dict[str, str]:
        return {"id": str(user.id), "email": user.email}

    return app


app = create_app()
