"""Standardized API error responses."""
from __future__ import annotations

from fastapi import HTTPException

# Map HTTP status codes to error type names
_STATUS_ERROR_MAP: dict[int, str] = {
    400: "BadRequest",
    401: "Unauthorized",
    403: "Forbidden",
    404: "NotFound",
    409: "Conflict",
    410: "Gone",
    422: "ValidationError",
    429: "TooManyRequests",
    500: "InternalServerError",
}


def error_detail(status_code: int, message: str, *, code: str | None = None) -> dict:
    """Build a standardized error detail dict.

    Format: {"error": "NotFound", "message": "Report not found", "detail": ..., "status_code": 404}
    When code is provided, detail is a dict with code and detail keys.
    """
    error_type = _STATUS_ERROR_MAP.get(status_code, "Error")
    if code is not None:
        detail_value: dict | str = {"code": code, "detail": message}
    else:
        detail_value = message
    return {
        "error": error_type,
        "message": message,
        "detail": detail_value,
        "status_code": status_code,
    }


def raise_error(status_code: int, message: str, *, code: str | None = None) -> None:
    """Raise an HTTPException with standardized error format."""
    raise HTTPException(
        status_code=status_code,
        detail=error_detail(status_code, message, code=code),
    )
