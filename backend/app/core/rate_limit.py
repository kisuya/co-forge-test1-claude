"""API rate limiting middleware."""
from __future__ import annotations

import logging
import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.exceptions import error_detail

logger = logging.getLogger(__name__)

# Per-endpoint rate limit rules: (max_requests, window_seconds)
ENDPOINT_LIMITS: dict[str, tuple[int, int]] = {
    "POST /api/auth/login": (5, 60),
    "POST /api/reports": (10, 60),
}

# Default limits
DEFAULT_AUTH_LIMIT = (60, 60)  # 60 requests per minute for authenticated
DEFAULT_ANON_LIMIT = (20, 60)  # 20 requests per minute for unauthenticated


class _SlidingWindowCounter:
    """Simple in-memory sliding window rate limiter."""

    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_rate_limited(self, key: str, max_requests: int, window: int) -> bool:
        """Check if the key has exceeded the rate limit."""
        now = time.time()
        cutoff = now - window
        # Remove expired entries
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        if len(self._requests[key]) >= max_requests:
            return True
        self._requests[key].append(now)
        return False

    def reset(self) -> None:
        """Clear all counters (for testing)."""
        self._requests.clear()


# Global counter instance
counter = _SlidingWindowCounter()


def _get_client_key(request: Request) -> str:
    """Get a rate limit key from the request."""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        return f"auth:{hash(auth)}"
    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"


def _get_limit(request: Request) -> tuple[int, int]:
    """Get the rate limit for the given request."""
    method = request.method
    path = request.url.path
    endpoint_key = f"{method} {path}"

    if endpoint_key in ENDPOINT_LIMITS:
        return ENDPOINT_LIMITS[endpoint_key]

    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        return DEFAULT_AUTH_LIMIT
    return DEFAULT_ANON_LIMIT


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window counters."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        client_key = _get_client_key(request)
        max_requests, window = _get_limit(request)

        # Include endpoint in key for per-endpoint limits
        method = request.method
        path = request.url.path
        endpoint_key = f"{method} {path}"
        if endpoint_key in ENDPOINT_LIMITS:
            rate_key = f"{client_key}:{endpoint_key}"
        else:
            rate_key = client_key

        if counter.is_rate_limited(rate_key, max_requests, window):
            return JSONResponse(
                status_code=429,
                content=error_detail(429, "Rate limit exceeded"),
                headers={"Retry-After": str(window)},
            )

        return await call_next(request)
