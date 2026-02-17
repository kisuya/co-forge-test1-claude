"""Structured logging configuration using structlog."""
from __future__ import annotations

import logging
import os
import uuid
import time
from contextvars import ContextVar
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Context variable to propagate request_id across the request lifecycle
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

_structlog_configured = False


def _get_log_level() -> str:
    """Return the log level based on environment."""
    raw = os.environ.get("LOG_LEVEL", "").upper()
    if raw in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        return raw
    debug = os.environ.get("DEBUG", "false").lower()
    if debug in ("true", "1", "yes"):
        return "DEBUG"
    return "INFO"


def configure_logging() -> None:
    """Configure structlog for JSON structured logging.

    Falls back to standard logging if structlog initialisation fails.
    """
    global _structlog_configured  # noqa: PLW0603
    if _structlog_configured:
        return

    log_level = _get_log_level()

    try:
        import structlog

        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        logging.basicConfig(
            format="%(message)s",
            level=getattr(logging, log_level),
        )
        _structlog_configured = True
    except Exception:
        # Fallback to standard logging
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
            level=getattr(logging, log_level),
        )
        logging.getLogger(__name__).warning(
            "structlog init failed, using standard logging"
        )


def get_logger(name: str | None = None) -> Any:
    """Return a structlog logger, or fallback to standard logger."""
    configure_logging()
    try:
        import structlog
        return structlog.get_logger(name)
    except Exception:
        return logging.getLogger(name)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs request/response with timing and request_id."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        rid = str(uuid.uuid4())
        request_id_var.set(rid)
        request.state.request_id = rid

        logger = get_logger("http")
        start = time.monotonic()

        try:
            import structlog
            structlog.contextvars.clear_contextvars()
            structlog.contextvars.bind_contextvars(request_id=rid)
        except Exception:
            pass

        logger.info(
            "request_started",
            method=request.method,
            path=str(request.url.path),
            request_id=rid,
        )

        response = await call_next(request)

        duration_ms = round((time.monotonic() - start) * 1000, 2)

        logger.info(
            "request_finished",
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_id=rid,
        )

        response.headers["X-Request-ID"] = rid
        return response
