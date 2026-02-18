"""Tests for multi-layer cause analysis (analysis-004).

Verifies:
- Multi-layer prompt generation with 3 cause categories
- Response parsing (direct_causes, indirect_causes, macro_factors)
- impact_level field in each cause
- Backward-compatible flat causes list
- analysis_service stores multi-layer structure in JSONB
- Existing old-format AnalysisResult still works (backward compat)
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

TEST_DB_URL = "sqlite:///test_multilayer_analysis.db"


def _setup():
    import app.models  # noqa: F401
    from app.db.database import create_tables
    create_tables(TEST_DB_URL)


def _teardown():
    from app.db.database import Base, get_engine, dispose_engine
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    dispose_engine(TEST_DB_URL)
    if os.path.exists("test_multilayer_analysis.db"):
        os.remove("test_multilayer_analysis.db")


def _get_session():
    from app.db.database import get_session_factory
    return get_session_factory(TEST_DB_URL)()


# ---- Prompt generation tests ----


def test_multilayer_prompt_contains_three_categories():
    """build_multilayer_prompt should include all 3 cause categories."""
    from app.clients.llm_client import build_multilayer_prompt

    prompt = build_multilayer_prompt("삼성전자", "005930", -5.2, "- 뉴스1")
    assert "직접 원인 (Direct)" in prompt
    assert "간접 원인 (Indirect)" in prompt
    assert "시장 환경 (Macro)" in prompt


def test_multilayer_prompt_contains_stock_info():
    """Prompt should contain stock name, code, and change_pct."""
    from app.clients.llm_client import build_multilayer_prompt

    prompt = build_multilayer_prompt("SK하이닉스", "000660", 3.8, "- 뉴스A")
    assert "SK하이닉스" in prompt
    assert "000660" in prompt
    assert "+3.8%" in prompt


def test_multilayer_prompt_contains_impact_level():
    """Prompt should request impact_level field."""
    from app.clients.llm_client import build_multilayer_prompt

    prompt = build_multilayer_prompt("삼성전자", "005930", -5.0, "")
    assert "impact_level" in prompt
    assert "critical" in prompt
    assert "significant" in prompt
    assert "minor" in prompt


def test_multilayer_prompt_contains_sources():
    """Prompt should include the source text."""
    from app.clients.llm_client import build_multilayer_prompt

    src = "- [news] 삼성전자 실적 발표 (https://example.com)"
    prompt = build_multilayer_prompt("삼성전자", "005930", -5.0, src)
    assert "삼성전자 실적 발표" in prompt


def test_multilayer_prompt_json_structure():
    """Prompt should include the expected JSON structure."""
    from app.clients.llm_client import build_multilayer_prompt

    prompt = build_multilayer_prompt("삼성전자", "005930", -5.0, "")
    assert "direct_causes" in prompt
    assert "indirect_causes" in prompt
    assert "macro_factors" in prompt


# ---- Response parsing tests ----


def test_parse_multilayer_response_full():
    """parse_multilayer_response should correctly parse a full response."""
    from app.clients.llm_client import parse_multilayer_response

    raw = json.dumps({
        "summary": "삼성전자 실적 부진으로 하락",
        "direct_causes": [
            {
                "reason": "3분기 실적 부진",
                "confidence": "high",
                "impact": "매출 감소로 주가 하락 압력",
                "impact_level": "critical",
            },
        ],
        "indirect_causes": [
            {
                "reason": "반도체 수요 둔화",
                "confidence": "medium",
                "impact": "산업 전반 약세",
                "impact_level": "significant",
            },
        ],
        "macro_factors": [
            {
                "reason": "미 금리 인상 우려",
                "confidence": "low",
                "impact": "성장주 전반 조정",
                "impact_level": "minor",
            },
        ],
    })
    result = parse_multilayer_response(raw)

    assert result.summary == "삼성전자 실적 부진으로 하락"
    assert len(result.direct_causes) == 1
    assert result.direct_causes[0].reason == "3분기 실적 부진"
    assert result.direct_causes[0].confidence == "high"
    assert result.direct_causes[0].impact_level == "critical"
    assert len(result.indirect_causes) == 1
    assert result.indirect_causes[0].impact_level == "significant"
    assert len(result.macro_factors) == 1
    assert result.macro_factors[0].impact_level == "minor"


def test_parse_multilayer_response_empty_categories():
    """parse_multilayer_response should handle empty categories."""
    from app.clients.llm_client import parse_multilayer_response

    raw = json.dumps({
        "summary": "원인 불명",
        "direct_causes": [],
        "indirect_causes": [],
        "macro_factors": [],
    })
    result = parse_multilayer_response(raw)

    assert result.summary == "원인 불명"
    assert len(result.direct_causes) == 0
    assert len(result.indirect_causes) == 0
    assert len(result.macro_factors) == 0


def test_parse_multilayer_response_missing_categories():
    """parse_multilayer_response should default missing categories to empty."""
    from app.clients.llm_client import parse_multilayer_response

    raw = json.dumps({
        "summary": "분석 요약",
        "direct_causes": [
            {"reason": "원인1", "confidence": "high", "impact": "영향1"},
        ],
    })
    result = parse_multilayer_response(raw)

    assert len(result.direct_causes) == 1
    assert len(result.indirect_causes) == 0
    assert len(result.macro_factors) == 0


def test_parse_multilayer_response_invalid_json():
    """parse_multilayer_response should handle invalid JSON gracefully."""
    from app.clients.llm_client import parse_multilayer_response

    result = parse_multilayer_response("This is not JSON")
    assert result.summary == "This is not JSON"
    assert len(result.direct_causes) == 0


def test_parse_multilayer_response_default_impact_level():
    """impact_level should default to 'significant' when not provided."""
    from app.clients.llm_client import parse_multilayer_response

    raw = json.dumps({
        "summary": "test",
        "direct_causes": [
            {"reason": "원인", "confidence": "high", "impact": "영향"},
        ],
    })
    result = parse_multilayer_response(raw)
    assert result.direct_causes[0].impact_level == "significant"


def test_parse_multilayer_response_default_confidence():
    """confidence should default to 'medium' when not provided."""
    from app.clients.llm_client import parse_multilayer_response

    raw = json.dumps({
        "summary": "test",
        "direct_causes": [
            {"reason": "원인", "impact": "영향"},
        ],
    })
    result = parse_multilayer_response(raw)
    assert result.direct_causes[0].confidence == "medium"


# ---- Backward compatibility tests ----


def test_multilayer_result_flat_causes():
    """MultiLayerAnalysisResult.causes should return flat list of all causes."""
    from app.clients.llm_client import MultiLayerAnalysisResult, MultiLayerCause

    result = MultiLayerAnalysisResult(
        summary="test",
        direct_causes=[
            MultiLayerCause(reason="직접1", confidence="high", impact="영향", impact_level="critical"),
        ],
        indirect_causes=[
            MultiLayerCause(reason="간접1", confidence="medium", impact="영향", impact_level="significant"),
        ],
        macro_factors=[
            MultiLayerCause(reason="거시1", confidence="low", impact="영향", impact_level="minor"),
        ],
    )

    flat = result.causes
    assert len(flat) == 3
    assert flat[0].reason == "직접1"
    assert flat[1].reason == "간접1"
    assert flat[2].reason == "거시1"


def test_multilayer_result_empty_causes():
    """MultiLayerAnalysisResult with no causes should return empty flat list."""
    from app.clients.llm_client import MultiLayerAnalysisResult

    result = MultiLayerAnalysisResult(summary="empty")
    assert len(result.causes) == 0


def test_old_analysis_result_still_works():
    """AnalysisResult (old format) should still be importable and functional."""
    from app.clients.llm_client import AnalysisCause, AnalysisResult

    result = AnalysisResult(
        summary="old format",
        causes=[
            AnalysisCause(reason="원인", confidence="high", impact="영향"),
        ],
    )
    assert result.summary == "old format"
    assert len(result.causes) == 1


# ---- analysis_service integration tests ----


def test_run_analysis_stores_multilayer_structure():
    """run_analysis should store multi-layer causes in report.analysis."""
    _setup()
    session = _get_session()
    try:
        from app.clients.llm_client import MultiLayerAnalysisResult, MultiLayerCause
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
            title="삼성전자 뉴스", url="https://example.com/1",
        )
        session.add(src)
        session.commit()

        def mock_analyze(name, code, change_pct, sources):
            return MultiLayerAnalysisResult(
                summary="삼성전자 하락 분석",
                direct_causes=[
                    MultiLayerCause(
                        reason="실적 부진", confidence="high",
                        impact="단기 하락", impact_level="critical",
                    ),
                ],
                indirect_causes=[
                    MultiLayerCause(
                        reason="반도체 산업 둔화", confidence="medium",
                        impact="중기 약세", impact_level="significant",
                    ),
                ],
                macro_factors=[
                    MultiLayerCause(
                        reason="금리 인상", confidence="low",
                        impact="성장주 조정", impact_level="minor",
                    ),
                ],
            )

        result = run_analysis(session, report, analyze_fn=mock_analyze)

        db_report = session.execute(
            select(Report).where(Report.id == report.id)
        ).scalar_one()

        analysis = db_report.analysis
        assert analysis["market"] == "KRX"

        # Multi-layer structure present
        assert "direct_causes" in analysis
        assert "indirect_causes" in analysis
        assert "macro_factors" in analysis

        assert len(analysis["direct_causes"]) == 1
        assert analysis["direct_causes"][0]["reason"] == "실적 부진"
        assert analysis["direct_causes"][0]["impact_level"] == "critical"

        assert len(analysis["indirect_causes"]) == 1
        assert analysis["indirect_causes"][0]["impact_level"] == "significant"

        assert len(analysis["macro_factors"]) == 1
        assert analysis["macro_factors"][0]["impact_level"] == "minor"

        # Backward-compatible flat causes also present
        assert "causes" in analysis
        assert len(analysis["causes"]) == 3

        assert db_report.status == "completed"
    finally:
        session.close()
        _teardown()


def test_run_analysis_backward_compat_with_old_result():
    """run_analysis should work with old AnalysisResult (no multi-layer)."""
    _setup()
    session = _get_session()
    try:
        from app.clients.llm_client import AnalysisCause, AnalysisResult
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

        def old_mock_analyze(name, code, change_pct, sources):
            return AnalysisResult(
                summary="old format test",
                causes=[
                    AnalysisCause(
                        reason="수요 증가", confidence="high", impact="상승",
                    ),
                ],
            )

        result = run_analysis(session, report, analyze_fn=old_mock_analyze)

        db_report = session.execute(
            select(Report).where(Report.id == report.id)
        ).scalar_one()

        analysis = db_report.analysis
        # Flat causes should still be present
        assert "causes" in analysis
        assert len(analysis["causes"]) == 1
        assert analysis["causes"][0]["reason"] == "수요 증가"

        # Multi-layer keys should NOT be present for old format
        assert "direct_causes" not in analysis

        assert db_report.status == "completed"
    finally:
        session.close()
        _teardown()


def test_run_analysis_no_sources_note():
    """run_analysis should add note when no sources."""
    _setup()
    session = _get_session()
    try:
        from app.clients.llm_client import MultiLayerAnalysisResult
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
            return MultiLayerAnalysisResult(summary="원인 불명")

        run_analysis(session, report, analyze_fn=mock_analyze)

        db_report = session.execute(
            select(Report).where(Report.id == report.id)
        ).scalar_one()

        assert db_report.analysis["note"] == "관련 뉴스를 찾지 못했습니다"
    finally:
        session.close()
        _teardown()


def test_multilayer_cause_impact_levels():
    """Each impact_level value should be valid."""
    from app.clients.llm_client import parse_multilayer_response

    raw = json.dumps({
        "summary": "test",
        "direct_causes": [
            {"reason": "a", "confidence": "high", "impact": "x", "impact_level": "critical"},
            {"reason": "b", "confidence": "high", "impact": "x", "impact_level": "significant"},
            {"reason": "c", "confidence": "high", "impact": "x", "impact_level": "minor"},
        ],
    })
    result = parse_multilayer_response(raw)
    levels = [c.impact_level for c in result.direct_causes]
    assert levels == ["critical", "significant", "minor"]


def test_parse_ignores_non_dict_causes():
    """Non-dict items in cause lists should be skipped."""
    from app.clients.llm_client import parse_multilayer_response

    raw = json.dumps({
        "summary": "test",
        "direct_causes": [
            "not a dict",
            {"reason": "valid", "confidence": "high", "impact": "ok"},
            42,
        ],
    })
    result = parse_multilayer_response(raw)
    assert len(result.direct_causes) == 1
    assert result.direct_causes[0].reason == "valid"


def test_analyze_stock_movement_no_api_key():
    """analyze_stock_movement should return empty result when no API key."""
    from unittest.mock import patch

    from app.clients.llm_client import analyze_stock_movement

    with patch("app.clients.llm_client.get_settings") as mock_settings:
        mock_settings.return_value.anthropic_api_key = ""
        result = analyze_stock_movement("삼성전자", "005930", -5.0, [])
        assert result.summary == "API key not configured"
        assert len(result.direct_causes) == 0
        assert len(result.indirect_causes) == 0
        assert len(result.macro_factors) == 0
