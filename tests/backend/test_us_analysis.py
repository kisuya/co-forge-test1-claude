"""Tests for US stock analysis report in Korean (analysis-003)."""
from __future__ import annotations

import os
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.clients.llm_client import AnalysisCause, AnalysisResult
from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import PriceSnapshot, Report, ReportSource
from app.models.stock import Stock
from app.services.analysis_service import US_MARKETS, _is_us_stock, run_analysis
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_us_analysis.db"


def _setup() -> Session:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    seed_stocks(session)
    seed_us_stocks(session)
    return session


def _teardown(session: Session | None = None) -> None:
    if session:
        session.close()
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_us_analysis.db"):
        os.remove("test_us_analysis.db")


def _mock_analyze(name: str, code: str, change_pct: float, sources: list) -> AnalysisResult:
    """Mock LLM analysis returning Korean content."""
    return AnalysisResult(
        summary=f"{name}({code}) {change_pct:+.1f}% 변동 분석",
        causes=[
            AnalysisCause(
                reason="실적 발표 이후 기대 상회",
                confidence="high",
                impact="주가 상승 압력",
            ),
        ],
    )


def _create_us_report(session: Session) -> tuple[Stock, Report]:
    """Create a report for AAPL."""
    stock = session.query(Stock).filter(Stock.code == "AAPL").first()
    assert stock is not None
    report = Report(
        stock_id=stock.id,
        trigger_price=Decimal("195.50"),
        trigger_change_pct=5.2,
        status="pending",
    )
    session.add(report)
    session.flush()
    return stock, report


def _create_kr_report(session: Session) -> tuple[Stock, Report]:
    """Create a report for Samsung (005930)."""
    stock = session.query(Stock).filter(Stock.code == "005930").first()
    assert stock is not None
    report = Report(
        stock_id=stock.id,
        trigger_price=Decimal("70000"),
        trigger_change_pct=4.0,
        status="pending",
    )
    session.add(report)
    session.flush()
    return stock, report


# --- US stock detection ---


def test_is_us_stock_nyse() -> None:
    """NYSE stock should be identified as US."""
    session = _setup()
    try:
        stock = session.query(Stock).filter(Stock.code == "AAPL").first()
        assert _is_us_stock(stock)
    finally:
        _teardown(session)


def test_is_us_stock_nasdaq() -> None:
    """NASDAQ stock should be identified as US."""
    session = _setup()
    try:
        stock = session.query(Stock).filter(Stock.code == "MSFT").first()
        assert _is_us_stock(stock)
    finally:
        _teardown(session)


def test_is_not_us_stock_krx() -> None:
    """KRX stock should not be identified as US."""
    session = _setup()
    try:
        stock = session.query(Stock).filter(Stock.code == "005930").first()
        assert not _is_us_stock(stock)
    finally:
        _teardown(session)


# --- Analysis with market field ---


def test_us_analysis_includes_market_field() -> None:
    """US stock analysis should include market field in analysis JSON."""
    session = _setup()
    try:
        stock, report = _create_us_report(session)
        session.commit()
        run_analysis(session, report, analyze_fn=_mock_analyze)
        assert report.analysis is not None
        assert "market" in report.analysis
        assert report.analysis["market"] in US_MARKETS
    finally:
        _teardown(session)


def test_kr_analysis_includes_market_field() -> None:
    """KRX stock analysis should include market=KRX."""
    session = _setup()
    try:
        stock, report = _create_kr_report(session)
        session.commit()
        run_analysis(session, report, analyze_fn=_mock_analyze)
        assert report.analysis is not None
        assert report.analysis["market"] == "KRX"
    finally:
        _teardown(session)


# --- Korean output ---


def test_us_analysis_summary_in_korean() -> None:
    """US stock analysis summary should be in Korean."""
    session = _setup()
    try:
        stock, report = _create_us_report(session)
        session.commit()
        result = run_analysis(session, report, analyze_fn=_mock_analyze)
        assert "분석" in result.summary or "변동" in result.summary
    finally:
        _teardown(session)


def test_us_analysis_causes_in_korean() -> None:
    """US stock analysis causes should be in Korean."""
    session = _setup()
    try:
        stock, report = _create_us_report(session)
        session.commit()
        result = run_analysis(session, report, analyze_fn=_mock_analyze)
        assert len(result.causes) > 0
        assert any("실적" in c.reason or "상승" in c.impact for c in result.causes)
    finally:
        _teardown(session)


# --- Same Report model ---


def test_us_report_uses_same_model() -> None:
    """US stock report should use the same Report model as KRX."""
    session = _setup()
    try:
        _, us_report = _create_us_report(session)
        _, kr_report = _create_kr_report(session)
        session.commit()

        run_analysis(session, us_report, analyze_fn=_mock_analyze)
        run_analysis(session, kr_report, analyze_fn=_mock_analyze)

        all_reports = session.query(Report).filter(Report.status == "completed").all()
        assert len(all_reports) == 2
    finally:
        _teardown(session)


# --- No sources note ---


def test_no_sources_adds_note() -> None:
    """Report with no sources should have note about missing news."""
    session = _setup()
    try:
        stock, report = _create_us_report(session)
        session.commit()
        run_analysis(session, report, analyze_fn=_mock_analyze)
        assert report.analysis is not None
        assert "note" in report.analysis
        assert "뉴스를 찾지 못했습니다" in report.analysis["note"]
    finally:
        _teardown(session)


def test_with_sources_no_note() -> None:
    """Report with sources should not have missing news note."""
    session = _setup()
    try:
        stock, report = _create_us_report(session)
        src = ReportSource(
            report_id=report.id,
            source_type="us_news",
            title="Apple beats earnings",
            url="https://news.example.com/apple",
        )
        session.add(src)
        session.commit()
        run_analysis(session, report, analyze_fn=_mock_analyze)
        assert report.analysis is not None
        assert "note" not in report.analysis
    finally:
        _teardown(session)


# --- Source types ---


def test_us_news_source_type() -> None:
    """US news sources should use source_type='us_news'."""
    session = _setup()
    try:
        stock, report = _create_us_report(session)
        src = ReportSource(
            report_id=report.id,
            source_type="us_news",
            title="Test news",
            url="https://example.com",
        )
        session.add(src)
        session.commit()
        sources = session.query(ReportSource).filter_by(
            report_id=report.id
        ).all()
        assert sources[0].source_type == "us_news"
    finally:
        _teardown(session)


# --- Completed status ---


def test_analysis_sets_completed_status() -> None:
    """run_analysis should set report status to 'completed'."""
    session = _setup()
    try:
        stock, report = _create_us_report(session)
        session.commit()
        run_analysis(session, report, analyze_fn=_mock_analyze)
        assert report.status == "completed"
    finally:
        _teardown(session)


# --- US_MARKETS constant ---


def test_us_markets_constant() -> None:
    """US_MARKETS should contain NYSE and NASDAQ."""
    assert "NYSE" in US_MARKETS
    assert "NASDAQ" in US_MARKETS
