"""Tests for end-to-end pipeline: price → spike → news → analysis → notify (pipe-006).

Verifies:
- Full pipeline chain execution with mocks
- Error isolation: failure in one step doesn't block others
- PipelineResult tracking (counts + errors + duration)
- Celery task and beat schedule registration
- Notification only for completed reports
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-ohmystock-must-be-at-least-32-bytes-long",
)

TEST_DB_URL = "sqlite:///test_e2e_pipeline.db"


def _setup():
    import app.models  # noqa: F401
    from app.db.database import create_tables
    create_tables(TEST_DB_URL)


def _teardown():
    from app.db.database import Base, get_engine, dispose_engine
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    dispose_engine(TEST_DB_URL)
    if os.path.exists("test_e2e_pipeline.db"):
        os.remove("test_e2e_pipeline.db")


def _get_session():
    from app.db.database import get_session_factory
    return get_session_factory(TEST_DB_URL)()


# ---- PipelineResult dataclass ----


def test_pipeline_result_defaults():
    """PipelineResult should have zero defaults."""
    from app.workers.e2e_pipeline import PipelineResult

    r = PipelineResult()
    assert r.prices_collected == 0
    assert r.spikes_detected == 0
    assert r.news_collected == 0
    assert r.reports_completed == 0
    assert r.notifications_sent == 0
    assert r.errors == []
    assert r.duration_ms == 0


def test_pipeline_result_with_values():
    """PipelineResult should store all fields."""
    from app.workers.e2e_pipeline import PipelineResult

    r = PipelineResult(
        prices_collected=10,
        spikes_detected=2,
        news_collected=5,
        reports_completed=2,
        notifications_sent=3,
        errors=["test error"],
        duration_ms=1500,
    )
    assert r.prices_collected == 10
    assert r.spikes_detected == 2
    assert r.reports_completed == 2
    assert len(r.errors) == 1


# ---- Full pipeline tests ----


def test_pipeline_full_success():
    """Full pipeline should work with all steps succeeding."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import Report
        from app.workers.e2e_pipeline import run_pipeline

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        # Mock report that gets "completed"
        mock_report = Report(
            stock_id=stock.id,
            trigger_price=Decimal("70000"),
            trigger_change_pct=-5.0,
            status="pending",
        )

        def mock_collect_prices(db):
            return 10

        def mock_detect_spikes(db):
            mock_report.status = "pending"
            return [mock_report]

        def mock_collect_news(db):
            return [1, 2, 3]

        def mock_run_analysis(db, report):
            report.status = "completed"

        @dataclass
        class MockPush:
            success: int = 1

        def mock_send_notif(db, stock_id, change_pct):
            return MockPush()

        result = run_pipeline(
            session,
            collect_prices_fn=mock_collect_prices,
            detect_spikes_fn=mock_detect_spikes,
            collect_news_fn=mock_collect_news,
            run_analysis_fn=mock_run_analysis,
            send_notifications_fn=mock_send_notif,
        )

        assert result.prices_collected == 10
        assert result.spikes_detected == 1
        assert result.news_collected == 3
        assert result.reports_completed == 1
        assert result.notifications_sent == 1
        assert result.errors == []
        assert result.duration_ms >= 0
    finally:
        session.close()
        _teardown()


def test_pipeline_no_spikes():
    """Pipeline with no spikes should still complete successfully."""
    _setup()
    session = _get_session()
    try:
        from app.workers.e2e_pipeline import run_pipeline

        result = run_pipeline(
            session,
            collect_prices_fn=lambda db: 5,
            detect_spikes_fn=lambda db: [],
            collect_news_fn=lambda db: [],
            run_analysis_fn=lambda db, r: None,
            send_notifications_fn=lambda db, sid, pct: None,
        )

        assert result.prices_collected == 5
        assert result.spikes_detected == 0
        assert result.reports_completed == 0
        assert result.notifications_sent == 0
        assert result.errors == []
    finally:
        session.close()
        _teardown()


# ---- Error isolation tests ----


def test_pipeline_price_collection_error_isolated():
    """Error in price collection should not block spike detection."""
    _setup()
    session = _get_session()
    try:
        from app.workers.e2e_pipeline import run_pipeline

        def failing_collect(db):
            raise RuntimeError("price API down")

        result = run_pipeline(
            session,
            collect_prices_fn=failing_collect,
            detect_spikes_fn=lambda db: [],
            collect_news_fn=lambda db: [],
        )

        assert result.prices_collected == 0
        assert len(result.errors) == 1
        assert "price API down" in result.errors[0]
        # Other steps still ran
        assert result.spikes_detected == 0
    finally:
        session.close()
        _teardown()


def test_pipeline_spike_detection_error_isolated():
    """Error in spike detection should not block news collection."""
    _setup()
    session = _get_session()
    try:
        from app.workers.e2e_pipeline import run_pipeline

        def failing_detect(db):
            raise RuntimeError("DB query failed")

        result = run_pipeline(
            session,
            collect_prices_fn=lambda db: 3,
            detect_spikes_fn=failing_detect,
            collect_news_fn=lambda db: [1],
        )

        assert result.prices_collected == 3
        assert result.spikes_detected == 0
        assert result.news_collected == 1
        assert len(result.errors) == 1
        assert "DB query failed" in result.errors[0]
    finally:
        session.close()
        _teardown()


def test_pipeline_news_collection_error_isolated():
    """Error in news collection should not block analysis."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import Report
        from app.workers.e2e_pipeline import run_pipeline

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        mock_report = Report(
            stock_id=stock.id,
            trigger_price=Decimal("70000"),
            trigger_change_pct=-5.0,
            status="pending",
        )

        def failing_news(db):
            raise RuntimeError("news API timeout")

        result = run_pipeline(
            session,
            collect_prices_fn=lambda db: 1,
            detect_spikes_fn=lambda db: [mock_report],
            collect_news_fn=failing_news,
            run_analysis_fn=lambda db, r: setattr(r, "status", "completed"),
            send_notifications_fn=lambda db, sid, pct: type("P", (), {"success": 0})(),
        )

        assert result.news_collected == 0
        assert result.reports_completed == 1
        assert len(result.errors) == 1
        assert "news API timeout" in result.errors[0]
    finally:
        session.close()
        _teardown()


def test_pipeline_analysis_error_isolated():
    """Error in analysis for one report should not affect others."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import Report
        from app.workers.e2e_pipeline import run_pipeline

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        report1 = Report(
            stock_id=stock.id,
            trigger_price=Decimal("70000"),
            trigger_change_pct=-5.0,
            status="pending",
        )
        report2 = Report(
            stock_id=stock.id,
            trigger_price=Decimal("71000"),
            trigger_change_pct=-4.0,
            status="pending",
        )

        call_count = [0]

        def partial_analysis(db, report):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("LLM API error")
            report.status = "completed"

        result = run_pipeline(
            session,
            collect_prices_fn=lambda db: 0,
            detect_spikes_fn=lambda db: [report1, report2],
            collect_news_fn=lambda db: [],
            run_analysis_fn=partial_analysis,
            send_notifications_fn=lambda db, sid, pct: type("P", (), {"success": 1})(),
        )

        assert result.spikes_detected == 2
        assert result.reports_completed == 1  # only second succeeded
        assert result.notifications_sent == 1  # notification for completed one
        assert len(result.errors) == 1
        assert "LLM API error" in result.errors[0]
    finally:
        session.close()
        _teardown()


def test_pipeline_notification_error_isolated():
    """Error in notification should not crash pipeline."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import Report
        from app.workers.e2e_pipeline import run_pipeline

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        mock_report = Report(
            stock_id=stock.id,
            trigger_price=Decimal("70000"),
            trigger_change_pct=-5.0,
            status="pending",
        )

        def failing_notify(db, sid, pct):
            raise RuntimeError("WebPush server error")

        result = run_pipeline(
            session,
            collect_prices_fn=lambda db: 1,
            detect_spikes_fn=lambda db: [mock_report],
            collect_news_fn=lambda db: [],
            run_analysis_fn=lambda db, r: setattr(r, "status", "completed"),
            send_notifications_fn=failing_notify,
        )

        assert result.reports_completed == 1
        assert result.notifications_sent == 0
        assert len(result.errors) == 1
        assert "WebPush server error" in result.errors[0]
    finally:
        session.close()
        _teardown()


def test_pipeline_multiple_errors():
    """Pipeline should accumulate errors from multiple stages."""
    _setup()
    session = _get_session()
    try:
        from app.workers.e2e_pipeline import run_pipeline

        result = run_pipeline(
            session,
            collect_prices_fn=lambda db: (_ for _ in ()).throw(RuntimeError("err1")),
            detect_spikes_fn=lambda db: (_ for _ in ()).throw(RuntimeError("err2")),
            collect_news_fn=lambda db: (_ for _ in ()).throw(RuntimeError("err3")),
        )

        assert len(result.errors) == 3
        assert "err1" in result.errors[0]
        assert "err2" in result.errors[1]
        assert "err3" in result.errors[2]
    finally:
        session.close()
        _teardown()


# ---- Duration tracking ----


def test_pipeline_tracks_duration():
    """Pipeline should track execution time in milliseconds."""
    _setup()
    session = _get_session()
    try:
        from app.workers.e2e_pipeline import run_pipeline
        import time

        def slow_collect(db):
            time.sleep(0.05)  # 50ms
            return 1

        result = run_pipeline(
            session,
            collect_prices_fn=slow_collect,
            detect_spikes_fn=lambda db: [],
            collect_news_fn=lambda db: [],
        )

        assert result.duration_ms >= 40  # at least ~40ms
    finally:
        session.close()
        _teardown()


# ---- Notification only for completed reports ----


def test_pipeline_skips_notification_for_incomplete():
    """Notifications should only be sent for completed reports."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import Report
        from app.workers.e2e_pipeline import run_pipeline

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        mock_report = Report(
            stock_id=stock.id,
            trigger_price=Decimal("70000"),
            trigger_change_pct=-5.0,
            status="pending",
        )

        notification_calls = []

        def track_notify(db, sid, pct):
            notification_calls.append(sid)
            return type("P", (), {"success": 1})()

        # Analysis does NOT set status to completed
        result = run_pipeline(
            session,
            collect_prices_fn=lambda db: 0,
            detect_spikes_fn=lambda db: [mock_report],
            collect_news_fn=lambda db: [],
            run_analysis_fn=lambda db, r: None,  # leaves status as "pending"
            send_notifications_fn=track_notify,
        )

        assert result.reports_completed == 0
        assert result.notifications_sent == 0
        assert len(notification_calls) == 0  # not called at all
    finally:
        session.close()
        _teardown()


# ---- Celery integration ----


def test_celery_beat_has_pipeline_schedule():
    """Celery beat schedule should include the e2e pipeline task."""
    from app.workers.celery_app import celery

    schedule = celery.conf.beat_schedule
    assert "run-e2e-pipeline" in schedule
    pipeline_config = schedule["run-e2e-pipeline"]
    assert pipeline_config["task"] == "run_e2e_pipeline_task"
    assert pipeline_config["options"]["queue"] == "pipeline"


def test_celery_pipeline_task_importable():
    """run_e2e_pipeline_task should be importable."""
    from app.workers.e2e_pipeline import run_e2e_pipeline_task
    assert run_e2e_pipeline_task is not None


def test_pipeline_result_importable():
    """PipelineResult should be importable."""
    from app.workers.e2e_pipeline import PipelineResult, run_pipeline
    assert PipelineResult is not None
    assert run_pipeline is not None


# ---- Pipeline module structure ----


def test_pipeline_module_has_logger():
    """e2e_pipeline module should use logging."""
    from app.workers import e2e_pipeline
    assert hasattr(e2e_pipeline, "logger")


def test_pipeline_run_function_signature():
    """run_pipeline should accept db and optional overrides."""
    import inspect
    from app.workers.e2e_pipeline import run_pipeline

    sig = inspect.signature(run_pipeline)
    params = list(sig.parameters.keys())
    assert "db" in params
    assert "collect_prices_fn" in params
    assert "detect_spikes_fn" in params
    assert "collect_news_fn" in params
    assert "run_analysis_fn" in params
    assert "send_notifications_fn" in params
