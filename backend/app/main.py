from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, contextmanager
from typing import Generator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.cases import router as cases_router
from app.api.deps import get_current_user
from app.api.push import router as push_router
from app.api.reports import router as reports_router
from app.api.stocks import router as stocks_router
from app.api.watchlist import router as watchlist_router
from app.config import get_settings
from app.db.database import create_tables, get_session_factory
from app.models.user import User
from app.services.stock_service import seed_stocks, seed_us_stocks

logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://ohmystock.kr",
    "https://www.ohmystock.kr",
]


@contextmanager
def _get_startup_session(database_url: str) -> Generator[Session, None, None]:
    """Create a short-lived session for startup tasks."""
    factory = get_session_factory(database_url)
    session = factory()
    try:
        yield session
    finally:
        session.close()


def _run_seed(database_url: str) -> None:
    """Run seed data on startup. Idempotent — skips if data exists."""
    try:
        create_tables(database_url)
        with _get_startup_session(database_url) as session:
            count = seed_stocks(session)
            if count > 0:
                logger.info("Seeded %d KRX stocks", count)
            else:
                logger.info("KRX stocks already seeded, skipping")
            us_count = seed_us_stocks(session)
            if us_count > 0:
                logger.info("Seeded %d US stocks", us_count)
            else:
                logger.info("US stocks already seeded, skipping")
    except Exception:
        logger.exception("Failed to seed stocks on startup")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        _run_seed(settings.database_url)
        yield

    app = FastAPI(
        title="oh-my-stock",
        description="AI-powered stock movement analysis service",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(stocks_router)
    app.include_router(watchlist_router)
    app.include_router(reports_router)
    app.include_router(push_router)
    app.include_router(cases_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/me")
    def me(user: User = Depends(get_current_user)) -> dict[str, str]:
        return {"id": str(user.id), "email": user.email}

    return app


app = create_app()
