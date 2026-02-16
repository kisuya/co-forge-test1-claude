"""Tests for similar case integration into report pipeline (case-003)."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.clients.llm_client import AnalysisCause, AnalysisResult
from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import PriceSnapshot, Report, ReportSource
from app.models.stock import Stock
from app.services.analysis_service import run_analysis

TEST_DB_URL = "sqlite:///test_case_report_integration.db"


def _setup() -> Session:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    return factory()


def _teardown(session: Session) -> None:
    session.close()
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_case_report_integration.db"):
        os.remove("test_case_report_integration.db")


def _mock_analyze(name: str, code: str, pct: float, sources: list) -> AnalysisResult:
    return AnalysisResult(
        summary=f"{name} 급변동 분석",
        causes=[AnalysisCause(reason="테스트 원인", confidence="high", impact="상승")],
    )


def _add_stock(session: Session, code: str = "005930") -> Stock:
    stock = Stock(code=code, name="삼성전자", market="KRX")
    session.add(stock)
    session.flush()
    return stock


def _add_report(session: Session, stock: Stock, pct: float = 5.0) -> Report:
    report = Report(
        stock_id=stock.id,
        trigger_price=Decimal("55000"),
        trigger_change_pct=pct,
        status="pending",
    )
    session.add(report)
    session.flush()
    return report


def _add_snapshot(
    session: Session, stock: Stock, change_pct: float, days_ago: int,
    price: Decimal = Decimal("50000"),
) -> PriceSnapshot:
    snap = PriceSnapshot(
        stock_id=stock.id, price=price, change_pct=change_pct,
        volume=100000, captured_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    session.add(snap)
    session.flush()
    return snap


# --- similar_cases in analysis output ---


def test_analysis_includes_similar_cases_key():
    """Report.analysis should include similar_cases key."""
    session = _setup()
    try:
        stock = _add_stock(session)
        report = _add_report(session, stock)
        session.commit()

        run_analysis(session, report, analyze_fn=_mock_analyze)

        assert "similar_cases" in report.analysis
    finally:
        _teardown(session)


def test_analysis_similar_cases_empty_when_no_data():
    """similar_cases should be [] when no historical data exists."""
    session = _setup()
    try:
        stock = _add_stock(session)
        report = _add_report(session, stock)
        session.commit()

        run_analysis(session, report, analyze_fn=_mock_analyze)

        assert report.analysis["similar_cases"] == []
    finally:
        _teardown(session)


def test_analysis_similar_cases_found():
    """similar_cases should contain matches when data exists."""
    session = _setup()
    try:
        stock = _add_stock(session)
        _add_snapshot(session, stock, 5.2, days_ago=60)
        report = _add_report(session, stock, pct=5.0)
        session.commit()

        run_analysis(session, report, analyze_fn=_mock_analyze)

        cases = report.analysis["similar_cases"]
        assert len(cases) >= 1
        assert "change_pct" in cases[0]
        assert "similarity_score" in cases[0]
    finally:
        _teardown(session)


def test_analysis_similar_cases_have_trends():
    """Each similar case should have trend_1w and trend_1m arrays."""
    session = _setup()
    try:
        stock = _add_stock(session)
        _add_snapshot(session, stock, 5.0, days_ago=60, price=Decimal("50000"))
        for i in range(5):
            _add_snapshot(
                session, stock, 0.5, days_ago=59 - i,
                price=Decimal("50000") + Decimal(str(i * 200)),
            )
        report = _add_report(session, stock, pct=5.0)
        session.commit()

        run_analysis(session, report, analyze_fn=_mock_analyze)

        cases = report.analysis["similar_cases"]
        assert len(cases) >= 1
        assert "trend_1w" in cases[0]
        assert "trend_1m" in cases[0]
        assert isinstance(cases[0]["trend_1w"], list)
    finally:
        _teardown(session)


def test_analysis_similar_case_trend_format():
    """Trend points should have day and change_pct fields."""
    session = _setup()
    try:
        stock = _add_stock(session)
        _add_snapshot(session, stock, 5.0, days_ago=60, price=Decimal("50000"))
        _add_snapshot(session, stock, 0.5, days_ago=59, price=Decimal("50500"))
        report = _add_report(session, stock, pct=5.0)
        session.commit()

        run_analysis(session, report, analyze_fn=_mock_analyze)

        cases = report.analysis["similar_cases"]
        if len(cases) > 0 and len(cases[0]["trend_1w"]) > 0:
            point = cases[0]["trend_1w"][0]
            assert "day" in point
            assert "change_pct" in point
    finally:
        _teardown(session)


def test_analysis_max_3_similar_cases():
    """similar_cases should have at most 3 entries."""
    session = _setup()
    try:
        stock = _add_stock(session)
        for i in range(10):
            _add_snapshot(session, stock, 5.0 + i * 0.1, days_ago=40 + i * 10)
        report = _add_report(session, stock, pct=5.0)
        session.commit()

        run_analysis(session, report, analyze_fn=_mock_analyze)

        cases = report.analysis["similar_cases"]
        assert len(cases) <= 3
    finally:
        _teardown(session)


def test_analysis_still_has_causes():
    """Report should still have causes from LLM analysis."""
    session = _setup()
    try:
        stock = _add_stock(session)
        report = _add_report(session, stock)
        session.commit()

        run_analysis(session, report, analyze_fn=_mock_analyze)

        assert "causes" in report.analysis
        assert len(report.analysis["causes"]) >= 1
    finally:
        _teardown(session)


def test_analysis_still_has_market():
    """Report should still have market field."""
    session = _setup()
    try:
        stock = _add_stock(session)
        report = _add_report(session, stock)
        session.commit()

        run_analysis(session, report, analyze_fn=_mock_analyze)

        assert report.analysis["market"] == "KRX"
    finally:
        _teardown(session)


def test_analysis_completed_status():
    """Report should be marked completed."""
    session = _setup()
    try:
        stock = _add_stock(session)
        report = _add_report(session, stock)
        session.commit()

        run_analysis(session, report, analyze_fn=_mock_analyze)

        assert report.status == "completed"
    finally:
        _teardown(session)


def test_analysis_no_sources_has_note_and_cases():
    """With no sources, both note and similar_cases should exist."""
    session = _setup()
    try:
        stock = _add_stock(session)
        report = _add_report(session, stock)
        session.commit()

        run_analysis(session, report, analyze_fn=_mock_analyze)

        assert report.analysis["note"] == "관련 뉴스를 찾지 못했습니다"
        assert "similar_cases" in report.analysis
    finally:
        _teardown(session)


def test_analysis_service_imports_similar_case():
    """analysis_service should import get_cases_with_trends."""
    import importlib
    mod = importlib.import_module("app.services.analysis_service")
    src = open(mod.__file__).read()
    assert "get_cases_with_trends" in src
    assert "similar_cases" in src
