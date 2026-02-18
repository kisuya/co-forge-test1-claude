"""Tests for short/medium term outlook analysis (analysis-005).

Verifies:
- Outlook prompt generation
- Outlook response parsing (short_term, medium_term)
- Sentiment values (bullish/bearish/neutral)
- Catalyst list parsing
- analysis_service stores outlook in JSONB
- Backward compatibility: existing reports without outlook
- Frontend rendering: outlook section, sentiment badges
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal

import pytest
from sqlalchemy import select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-ohmystock-must-be-at-least-32-bytes-long",
)

TEST_DB_URL = "sqlite:///test_outlook_analysis.db"


def _setup():
    import app.models  # noqa: F401
    from app.db.database import create_tables
    create_tables(TEST_DB_URL)


def _teardown():
    from app.db.database import Base, get_engine, dispose_engine
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    dispose_engine(TEST_DB_URL)
    if os.path.exists("test_outlook_analysis.db"):
        os.remove("test_outlook_analysis.db")


def _get_session():
    from app.db.database import get_session_factory
    return get_session_factory(TEST_DB_URL)()


# ---- Prompt tests ----


def test_prompt_contains_outlook_section():
    """build_multilayer_prompt should include outlook instructions."""
    from app.clients.llm_client import build_multilayer_prompt

    prompt = build_multilayer_prompt("삼성전자", "005930", -5.0, "")
    assert "short_term" in prompt
    assert "medium_term" in prompt
    assert "sentiment" in prompt
    assert "catalysts" in prompt
    assert "bullish" in prompt
    assert "bearish" in prompt
    assert "neutral" in prompt


def test_prompt_mentions_timeframes():
    """Prompt should mention 1-week and 1-month timeframes."""
    from app.clients.llm_client import build_multilayer_prompt

    prompt = build_multilayer_prompt("삼성전자", "005930", -5.0, "")
    assert "1주" in prompt
    assert "1개월" in prompt


# ---- Parsing tests ----


def test_parse_outlook_full():
    """parse_multilayer_response should parse full outlook."""
    from app.clients.llm_client import parse_multilayer_response

    raw = json.dumps({
        "summary": "test",
        "direct_causes": [],
        "indirect_causes": [],
        "macro_factors": [],
        "short_term": {
            "summary": "1주 내 반등 예상",
            "sentiment": "bullish",
            "catalysts": ["실적 발표 기대", "기관 매수"],
        },
        "medium_term": {
            "summary": "1개월간 횡보 전망",
            "sentiment": "neutral",
            "catalysts": ["금리 동결 가능성"],
        },
    })
    result = parse_multilayer_response(raw)

    assert result.short_term_outlook is not None
    assert result.short_term_outlook.summary == "1주 내 반등 예상"
    assert result.short_term_outlook.sentiment == "bullish"
    assert len(result.short_term_outlook.catalysts) == 2
    assert "실적 발표 기대" in result.short_term_outlook.catalysts

    assert result.medium_term_outlook is not None
    assert result.medium_term_outlook.summary == "1개월간 횡보 전망"
    assert result.medium_term_outlook.sentiment == "neutral"
    assert len(result.medium_term_outlook.catalysts) == 1


def test_parse_outlook_bearish():
    """parse_multilayer_response should parse bearish outlook."""
    from app.clients.llm_client import parse_multilayer_response

    raw = json.dumps({
        "summary": "test",
        "direct_causes": [],
        "short_term": {
            "summary": "추가 하락 가능",
            "sentiment": "bearish",
            "catalysts": ["실적 악화"],
        },
    })
    result = parse_multilayer_response(raw)

    assert result.short_term_outlook is not None
    assert result.short_term_outlook.sentiment == "bearish"


def test_parse_outlook_missing():
    """parse_multilayer_response should handle missing outlook."""
    from app.clients.llm_client import parse_multilayer_response

    raw = json.dumps({
        "summary": "no outlook",
        "direct_causes": [],
    })
    result = parse_multilayer_response(raw)

    assert result.short_term_outlook is None
    assert result.medium_term_outlook is None


def test_parse_outlook_empty_summary():
    """Outlook with empty summary should be None."""
    from app.clients.llm_client import parse_multilayer_response

    raw = json.dumps({
        "summary": "test",
        "short_term": {"summary": "", "sentiment": "neutral"},
    })
    result = parse_multilayer_response(raw)
    assert result.short_term_outlook is None


def test_parse_outlook_invalid_sentiment():
    """Invalid sentiment should default to neutral."""
    from app.clients.llm_client import _parse_outlook

    result = _parse_outlook({
        "summary": "test",
        "sentiment": "unknown_value",
        "catalysts": [],
    })
    assert result is not None
    assert result.sentiment == "neutral"


def test_parse_outlook_non_dict():
    """Non-dict outlook should be None."""
    from app.clients.llm_client import _parse_outlook

    assert _parse_outlook(None) is None
    assert _parse_outlook("string") is None
    assert _parse_outlook(42) is None


def test_parse_outlook_catalysts_non_list():
    """Non-list catalysts should default to empty."""
    from app.clients.llm_client import _parse_outlook

    result = _parse_outlook({
        "summary": "test",
        "sentiment": "bullish",
        "catalysts": "not a list",
    })
    assert result is not None
    assert result.catalysts == []


def test_parse_outlook_catalysts_filters_empty():
    """Empty catalyst strings should be filtered out."""
    from app.clients.llm_client import _parse_outlook

    result = _parse_outlook({
        "summary": "test",
        "sentiment": "neutral",
        "catalysts": ["valid", "", None, "also valid"],
    })
    assert result is not None
    assert result.catalysts == ["valid", "also valid"]


# ---- Dataclass tests ----


def test_outlook_result_defaults():
    """OutlookResult should have proper defaults."""
    from app.clients.llm_client import OutlookResult

    o = OutlookResult()
    assert o.summary == ""
    assert o.sentiment == "neutral"
    assert o.catalysts == []


def test_multilayer_result_outlook_defaults():
    """MultiLayerAnalysisResult should default outlook to None."""
    from app.clients.llm_client import MultiLayerAnalysisResult

    result = MultiLayerAnalysisResult(summary="test")
    assert result.short_term_outlook is None
    assert result.medium_term_outlook is None


# ---- analysis_service integration ----


def test_run_analysis_stores_outlook():
    """run_analysis should store outlook in report.analysis."""
    _setup()
    session = _get_session()
    try:
        from app.clients.llm_client import (
            MultiLayerAnalysisResult, OutlookResult,
        )
        from app.models.report import Report, ReportSource
        from app.models.stock import Stock
        from app.services.analysis_service import run_analysis

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        report = Report(
            stock_id=stock.id,
            trigger_price=Decimal("70000"),
            trigger_change_pct=-5.0,
            status="generating",
        )
        session.add(report)
        session.flush()

        src = ReportSource(
            report_id=report.id, source_type="news",
            title="뉴스", url="https://example.com",
        )
        session.add(src)
        session.commit()

        def mock_analyze(name, code, change_pct, sources):
            return MultiLayerAnalysisResult(
                summary="하락 분석",
                short_term_outlook=OutlookResult(
                    summary="단기 반등 기대",
                    sentiment="bullish",
                    catalysts=["기관 매수", "저가 매수"],
                ),
                medium_term_outlook=OutlookResult(
                    summary="중기 횡보",
                    sentiment="neutral",
                    catalysts=["실적 확인 필요"],
                ),
            )

        run_analysis(session, report, analyze_fn=mock_analyze)

        db_report = session.execute(
            select(Report).where(Report.id == report.id)
        ).scalar_one()

        analysis = db_report.analysis
        assert "outlook" in analysis

        outlook = analysis["outlook"]
        assert "short_term" in outlook
        assert outlook["short_term"]["summary"] == "단기 반등 기대"
        assert outlook["short_term"]["sentiment"] == "bullish"
        assert len(outlook["short_term"]["catalysts"]) == 2

        assert "medium_term" in outlook
        assert outlook["medium_term"]["summary"] == "중기 횡보"
        assert outlook["medium_term"]["sentiment"] == "neutral"
    finally:
        session.close()
        _teardown()


def test_run_analysis_no_outlook():
    """run_analysis should not add outlook key when result has no outlook."""
    _setup()
    session = _get_session()
    try:
        from app.clients.llm_client import MultiLayerAnalysisResult
        from app.models.report import Report
        from app.models.stock import Stock
        from app.services.analysis_service import run_analysis

        stock = Stock(code="000660", name="SK하이닉스", market="KRX")
        session.add(stock)
        session.flush()

        report = Report(
            stock_id=stock.id,
            trigger_price=Decimal("130000"),
            trigger_change_pct=4.0,
            status="generating",
        )
        session.add(report)
        session.commit()

        def mock_analyze(name, code, change_pct, sources):
            return MultiLayerAnalysisResult(summary="no outlook")

        run_analysis(session, report, analyze_fn=mock_analyze)

        db_report = session.execute(
            select(Report).where(Report.id == report.id)
        ).scalar_one()

        assert "outlook" not in db_report.analysis
    finally:
        session.close()
        _teardown()


def test_run_analysis_partial_outlook():
    """run_analysis should store only available outlook (short_term only)."""
    _setup()
    session = _get_session()
    try:
        from app.clients.llm_client import (
            MultiLayerAnalysisResult, OutlookResult,
        )
        from app.models.report import Report
        from app.models.stock import Stock
        from app.services.analysis_service import run_analysis

        stock = Stock(code="035720", name="카카오", market="KRX")
        session.add(stock)
        session.flush()

        report = Report(
            stock_id=stock.id,
            trigger_price=Decimal("50000"),
            trigger_change_pct=-3.0,
            status="generating",
        )
        session.add(report)
        session.commit()

        def mock_analyze(name, code, change_pct, sources):
            return MultiLayerAnalysisResult(
                summary="partial",
                short_term_outlook=OutlookResult(
                    summary="short only", sentiment="bearish", catalysts=[],
                ),
            )

        run_analysis(session, report, analyze_fn=mock_analyze)

        db_report = session.execute(
            select(Report).where(Report.id == report.id)
        ).scalar_one()

        outlook = db_report.analysis.get("outlook", {})
        assert "short_term" in outlook
        assert outlook["short_term"]["sentiment"] == "bearish"
        assert "medium_term" not in outlook
    finally:
        session.close()
        _teardown()


# ---- Frontend rendering tests (structure) ----


def test_report_view_contains_outlook_section():
    """ReportView.tsx should have outlook section rendering."""
    import pathlib
    component_path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "components" / "ReportView.tsx"
    content = component_path.read_text()
    assert "outlook-section" in content
    assert "전망" in content


def test_report_view_has_sentiment_badges():
    """ReportView.tsx should render sentiment badges."""
    import pathlib
    component_path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "components" / "ReportView.tsx"
    content = component_path.read_text()
    assert "sentimentLabel" in content
    assert "sentimentColor" in content
    assert "bullish" in content
    assert "bearish" in content
    assert "neutral" in content


def test_report_view_outlook_graceful_fallback():
    """ReportView.tsx should not render outlook when missing."""
    import pathlib
    component_path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "components" / "ReportView.tsx"
    content = component_path.read_text()
    # Should check for outlook existence before rendering
    assert "outlook?.short_term" in content or "outlook.short_term" in content


def test_frontend_types_include_outlook():
    """Frontend types should include OutlookItem and AnalysisOutlook."""
    import pathlib
    types_path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "types" / "index.ts"
    content = types_path.read_text()
    assert "OutlookItem" in content
    assert "AnalysisOutlook" in content
    assert "short_term" in content
    assert "medium_term" in content
    assert '"bullish"' in content
    assert '"bearish"' in content
    assert '"neutral"' in content


def test_frontend_types_outlook_optional():
    """AnalysisResult should have optional outlook field."""
    import pathlib
    types_path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "types" / "index.ts"
    content = types_path.read_text()
    assert "outlook?: AnalysisOutlook" in content


def test_report_view_catalyst_list():
    """ReportView should render catalyst bullet list."""
    import pathlib
    component_path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "components" / "ReportView.tsx"
    content = component_path.read_text()
    assert "catalysts" in content
