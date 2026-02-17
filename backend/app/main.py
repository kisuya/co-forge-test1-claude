from __future__ import annotations

import logging
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, contextmanager
from typing import Generator

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import error_detail
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.api.auth import router as auth_router
from app.api.cases import router as cases_router
from app.api.deps import get_current_user
from app.api.discussions import router as discussions_router
from app.api.profile import router as profile_router
from app.api.push import router as push_router
from app.api.reports import router as reports_router
from app.api.share import router as share_router
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

    configure_logging()

    app.add_middleware(RequestLoggingMiddleware)

    app.add_middleware(RateLimitMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _cors_headers(request: Request) -> dict[str, str]:
        """Build CORS headers for error responses based on request origin."""
        origin = request.headers.get("origin", "")
        if origin in ALLOWED_ORIGINS:
            return {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        return {}

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail and "status_code" in detail:
            content = detail
        elif isinstance(detail, str):
            content = error_detail(exc.status_code, detail)
        else:
            content = error_detail(exc.status_code, str(detail))
        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=_cors_headers(request),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        content = error_detail(422, "Validation error")
        content["details"] = exc.errors()
        return JSONResponse(
            status_code=422,
            content=content,
            headers=_cors_headers(request),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content=error_detail(500, "Internal server error"),
            headers=_cors_headers(request),
        )

    app.include_router(auth_router)
    app.include_router(stocks_router)
    app.include_router(watchlist_router)
    app.include_router(reports_router)
    app.include_router(push_router)
    app.include_router(cases_router)
    app.include_router(share_router)
    app.include_router(profile_router)
    app.include_router(discussions_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/me")
    def me(user: User = Depends(get_current_user)) -> dict[str, str]:
        return {"id": str(user.id), "email": user.email}

    return app


app = create_app()
