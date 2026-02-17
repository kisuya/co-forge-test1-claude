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


def error_detail(status_code: int, message: str) -> dict:
    """Build a standardized error detail dict.

    Format: {"error": "NotFound", "message": "Report not found", "status_code": 404}
    """
    error_type = _STATUS_ERROR_MAP.get(status_code, "Error")
    return {
        "error": error_type,
        "message": message,
        "status_code": status_code,
    }


def raise_error(status_code: int, message: str) -> None:
    """Raise an HTTPException with standardized error format."""
    raise HTTPException(
        status_code=status_code,
        detail=error_detail(status_code, message),
    )
