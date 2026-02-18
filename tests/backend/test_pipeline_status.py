"""Tests for pipeline monitoring and status API (pipe-005).

Verifies:
- Pipeline status endpoint (GET /api/admin/pipeline-status)
- Redis-backed status retrieval
- Failure count tracking
- Consecutive failure log escalation
- Authentication requirement
- Redis unavailable fallback
"""
from __future__ import annotations

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-ohmystock-must-be-at-least-32-bytes-long",
)


# --- Pipeline Status Logic Tests ---


def test_pipeline_collectors_registered():
    """PIPELINE_COLLECTORS should list all collectors."""
    from app.api.pipeline_status import PIPELINE_COLLECTORS

    names = [c["name"] for c in PIPELINE_COLLECTORS]
    assert "krx_prices" in names
    assert "us_prices" in names
    assert "dart_disclosures" in names
    assert "stock_news" in names


def test_get_all_pipeline_statuses_no_redis():
    """get_all_pipeline_statuses should return unknown status when Redis unavailable."""
    from app.api.pipeline_status import get_all_pipeline_statuses

    with patch("app.api.pipeline_status._get_pipeline_status_from_redis", return_value=None), \
         patch("app.api.pipeline_status._get_failure_count", return_value=0):
        results = get_all_pipeline_statuses()

    assert len(results) >= 4
    for r in results:
        assert r["status"] == "unknown"
        assert r["last_run_at"] is None
        assert r["items_collected"] == 0


def test_get_all_pipeline_statuses_with_data():
    """get_all_pipeline_statuses should return data from Redis."""
    from app.api.pipeline_status import get_all_pipeline_statuses

    mock_status = {
        "status": "ok",
        "items_collected": 30,
        "last_run_at": "2026-02-18T10:00:00+00:00",
    }

    def mock_redis_get(name):
        if name == "krx_prices":
            return mock_status
        return None

    with patch("app.api.pipeline_status._get_pipeline_status_from_redis", side_effect=mock_redis_get), \
         patch("app.api.pipeline_status._get_failure_count", return_value=0):
        results = get_all_pipeline_statuses()

    krx = next(r for r in results if r["name"] == "krx_prices")
    assert krx["status"] == "ok"
    assert krx["items_collected"] == 30
    assert krx["last_run_at"] == "2026-02-18T10:00:00+00:00"


def test_get_all_pipeline_statuses_failure_status():
    """get_all_pipeline_statuses should show error status."""
    from app.api.pipeline_status import get_all_pipeline_statuses

    mock_status = {
        "status": "error",
        "items_collected": 0,
        "last_run_at": "2026-02-18T09:00:00+00:00",
    }

    with patch("app.api.pipeline_status._get_pipeline_status_from_redis", return_value=mock_status), \
         patch("app.api.pipeline_status._get_failure_count", return_value=2):
        results = get_all_pipeline_statuses()

    for r in results:
        assert r["status"] == "error"
        assert r["consecutive_failures"] == 2


def test_consecutive_failure_threshold():
    """Should escalate to ERROR log level after CONSECUTIVE_FAILURE_THRESHOLD failures."""
    from app.api.pipeline_status import get_all_pipeline_statuses, CONSECUTIVE_FAILURE_THRESHOLD

    assert CONSECUTIVE_FAILURE_THRESHOLD == 3

    with patch("app.api.pipeline_status._get_pipeline_status_from_redis", return_value=None), \
         patch("app.api.pipeline_status._get_failure_count", return_value=3), \
         patch("app.api.pipeline_status.logger") as mock_logger:
        results = get_all_pipeline_statuses()

    # Should have called logger.error for each collector with >= 3 failures
    assert mock_logger.error.call_count == len(results)


# --- Redis Integration Tests ---


def test_get_pipeline_status_from_redis_success():
    """_get_pipeline_status_from_redis should parse JSON from Redis."""
    from app.api.pipeline_status import _get_pipeline_status_from_redis

    mock_data = json.dumps({"status": "ok", "items_collected": 10})
    mock_client = MagicMock()
    mock_client.get.return_value = mock_data

    with patch("app.core.cache.get_redis_client", return_value=mock_client):
        result = _get_pipeline_status_from_redis("krx_prices")

    assert result is not None
    assert result["status"] == "ok"
    assert result["items_collected"] == 10


def test_get_pipeline_status_from_redis_no_data():
    """_get_pipeline_status_from_redis should return None when no data."""
    from app.api.pipeline_status import _get_pipeline_status_from_redis

    mock_client = MagicMock()
    mock_client.get.return_value = None

    with patch("app.core.cache.get_redis_client", return_value=mock_client):
        result = _get_pipeline_status_from_redis("krx_prices")

    assert result is None


def test_get_pipeline_status_from_redis_no_client():
    """_get_pipeline_status_from_redis should return None when Redis unavailable."""
    from app.api.pipeline_status import _get_pipeline_status_from_redis

    with patch("app.core.cache.get_redis_client", return_value=None):
        result = _get_pipeline_status_from_redis("krx_prices")

    assert result is None


def test_get_pipeline_status_from_redis_exception():
    """_get_pipeline_status_from_redis should return None on exceptions."""
    from app.api.pipeline_status import _get_pipeline_status_from_redis

    with patch("app.core.cache.get_redis_client", side_effect=Exception("Redis down")):
        result = _get_pipeline_status_from_redis("krx_prices")

    assert result is None


def test_get_failure_count_from_redis():
    """_get_failure_count should read from Redis."""
    from app.api.pipeline_status import _get_failure_count

    mock_client = MagicMock()
    mock_client.get.return_value = "5"

    with patch("app.core.cache.get_redis_client", return_value=mock_client):
        count = _get_failure_count("krx_prices")

    assert count == 5


def test_get_failure_count_no_data():
    """_get_failure_count should return 0 when no data."""
    from app.api.pipeline_status import _get_failure_count

    mock_client = MagicMock()
    mock_client.get.return_value = None

    with patch("app.core.cache.get_redis_client", return_value=mock_client):
        count = _get_failure_count("krx_prices")

    assert count == 0


def test_get_failure_count_exception():
    """_get_failure_count should return 0 on exceptions."""
    from app.api.pipeline_status import _get_failure_count

    with patch("app.core.cache.get_redis_client", side_effect=Exception("Redis down")):
        count = _get_failure_count("krx_prices")

    assert count == 0


# --- API Endpoint Tests ---


def test_pipeline_status_endpoint_requires_auth():
    """GET /api/admin/pipeline-status should require authentication."""
    from httpx import ASGITransport, AsyncClient
    from app.main import create_app
    import asyncio

    test_app = create_app()

    async def _test():
        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as client:
            resp = await client.get("/api/admin/pipeline-status")
            assert resp.status_code in (401, 403)

    asyncio.get_event_loop().run_until_complete(_test())


def test_pipeline_status_response_structure():
    """Pipeline status response should have expected structure."""
    from app.api.pipeline_status import get_all_pipeline_statuses

    with patch("app.api.pipeline_status._get_pipeline_status_from_redis", return_value=None), \
         patch("app.api.pipeline_status._get_failure_count", return_value=0):
        results = get_all_pipeline_statuses()

    for collector in results:
        assert "name" in collector
        assert "description" in collector
        assert "task" in collector
        assert "last_run_at" in collector
        assert "status" in collector
        assert "items_collected" in collector
        assert "consecutive_failures" in collector


# --- Module-Level Tests ---


def test_pipeline_status_module_has_router():
    """pipeline_status module should export a router."""
    from app.api.pipeline_status import router
    assert router is not None


def test_pipeline_status_registered_in_app():
    """Pipeline status router should be registered in the FastAPI app."""
    from app.main import app

    routes = [r.path for r in app.routes]
    assert "/api/admin/pipeline-status" in routes


def test_pipeline_status_has_all_expected_collectors():
    """Pipeline status should include all 4 pipeline collectors."""
    from app.api.pipeline_status import PIPELINE_COLLECTORS

    assert len(PIPELINE_COLLECTORS) >= 4
    tasks = [c["task"] for c in PIPELINE_COLLECTORS]
    assert "collect_krx_prices_task" in tasks
    assert "collect_us_prices_task" in tasks
    assert "collect_dart_disclosures_task" in tasks
    assert "collect_stock_news_task" in tasks
