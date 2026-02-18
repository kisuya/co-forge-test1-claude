"""Tests for enhanced report UI (analysis-009).

Verifies:
- Multi-layer cause tabs (direct/indirect/macro)
- Impact level badges (critical/significant/minor)
- Graceful fallback for old reports (flat causes)
- Outlook section rendering
- Sector impact section rendering
- Similar cases with aftermath
- Empty section handling
"""
import os
import pathlib

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
REPORT_VIEW = pathlib.Path(BASE) / "components" / "ReportView.tsx"
SIMILAR_CASES = pathlib.Path(BASE) / "components" / "SimilarCases.tsx"
TYPES_FILE = pathlib.Path(BASE) / "types" / "index.ts"


def _read(path: pathlib.Path) -> str:
    return path.read_text()


# ---- Multi-layer cause tabs ----


def test_report_view_has_cause_tabs():
    """ReportView should have tab buttons for direct/indirect/macro causes."""
    content = _read(REPORT_VIEW)
    assert "cause-tabs" in content
    assert "cause-tab-" in content
    assert '"direct"' in content
    assert '"indirect"' in content
    assert '"macro"' in content


def test_report_view_tab_labels():
    """Tabs should have Korean labels for 3 cause layers."""
    content = _read(REPORT_VIEW)
    assert "직접 원인" in content
    assert "간접 원인" in content
    assert "시장 환경" in content


def test_report_view_multilayer_causes_section():
    """MultiLayerCauses component should exist with testid."""
    content = _read(REPORT_VIEW)
    assert "multilayer-causes" in content
    assert "MultiLayerCauses" in content


def test_report_view_cause_panel_per_tab():
    """Each tab should have a cause panel with testid."""
    content = _read(REPORT_VIEW)
    assert "cause-panel-" in content


def test_report_view_empty_panel_message():
    """Empty panel should show a message."""
    content = _read(REPORT_VIEW)
    assert "해당 카테고리의 원인이 없습니다" in content


# ---- Impact level badges ----


def test_report_view_impact_level_badge():
    """Cause cards should have impact_level badge."""
    content = _read(REPORT_VIEW)
    assert "impact-level-badge" in content


def test_report_view_impact_level_labels():
    """Impact level labels should be in Korean."""
    content = _read(REPORT_VIEW)
    assert "심각" in content   # critical
    assert "중요" in content   # significant
    assert "경미" in content   # minor


def test_report_view_impact_level_colors():
    """Impact level badges should have distinct colors."""
    content = _read(REPORT_VIEW)
    assert "bg-red-100" in content     # critical
    assert "bg-orange-100" in content  # significant


# ---- Graceful fallback for old reports ----


def test_report_view_flat_causes_fallback():
    """Old reports without multi-layer causes should use flat cause display."""
    content = _read(REPORT_VIEW)
    assert "flat-causes" in content
    assert "cause-card-flat" in content


def test_report_view_has_multilayer_check():
    """ReportView should check for multi-layer data presence."""
    content = _read(REPORT_VIEW)
    assert "hasMultiLayerCauses" in content
    assert "isMultiLayer" in content


def test_report_view_conditional_rendering():
    """Should conditionally render multi-layer or flat causes."""
    content = _read(REPORT_VIEW)
    # Multi-layer path
    assert "isMultiLayer" in content
    assert "MultiLayerCauses" in content
    # Flat path
    assert "FlatCauseCard" in content


# ---- Outlook section ----


def test_report_view_outlook_section():
    """Outlook section should exist with testid."""
    content = _read(REPORT_VIEW)
    assert "outlook-section" in content
    assert "OutlookCard" in content


def test_report_view_outlook_sentiments():
    """Outlook should display sentiment labels."""
    content = _read(REPORT_VIEW)
    assert "긍정적" in content  # bullish
    assert "부정적" in content  # bearish
    assert "중립" in content    # neutral


def test_report_view_outlook_catalysts():
    """Outlook cards should render catalyst list."""
    content = _read(REPORT_VIEW)
    assert "catalysts" in content


# ---- Sector impact section ----


def test_report_view_sector_impact_section():
    """Sector impact section should exist with testid."""
    content = _read(REPORT_VIEW)
    assert "sector-impact-section" in content
    assert "sector-related-stock" in content


def test_report_view_sector_labels():
    """Sector section should have Korean labels."""
    content = _read(REPORT_VIEW)
    assert "섹터 영향" in content


# ---- Similar cases & aftermath ----


def test_similar_cases_aftermath_section():
    """SimilarCases should render aftermath."""
    content = _read(SIMILAR_CASES)
    assert "case-aftermath" in content
    assert "이후 추이" in content


def test_similar_cases_aftermath_fields():
    """SimilarCases should show 1w/1m returns and recovery days."""
    content = _read(SIMILAR_CASES)
    assert "after_1w_pct" in content
    assert "after_1m_pct" in content
    assert "recovery_days" in content
    assert "회복까지" in content


# ---- Types ----


def test_types_multilayer_cause():
    """Types should include MultiLayerCause with impact_level."""
    content = _read(TYPES_FILE)
    assert "MultiLayerCause" in content
    assert "impact_level" in content


def test_types_analysis_result_multilayer():
    """AnalysisResult should have optional multi-layer fields."""
    content = _read(TYPES_FILE)
    assert "direct_causes?" in content
    assert "indirect_causes?" in content
    assert "macro_factors?" in content


def test_types_outlook():
    """Types should include outlook types."""
    content = _read(TYPES_FILE)
    assert "OutlookItem" in content
    assert "AnalysisOutlook" in content


def test_types_sector_impact():
    """Types should include sector impact types."""
    content = _read(TYPES_FILE)
    assert "SectorImpact" in content
    assert "SectorRelatedStock" in content


def test_types_case_aftermath():
    """Types should include CaseAftermath."""
    content = _read(TYPES_FILE)
    assert "CaseAftermath" in content
    assert "after_1w_pct" in content
    assert "after_1m_pct" in content
    assert "recovery_days" in content


# ---- ReportView imports ----


def test_report_view_imports_types():
    """ReportView should import MultiLayerCause and AnalysisCause."""
    content = _read(REPORT_VIEW)
    assert "MultiLayerCause" in content
    assert "AnalysisCause" in content


def test_report_view_uses_state():
    """ReportView should use useState for tab state."""
    content = _read(REPORT_VIEW)
    assert "useState" in content
    assert "activeTab" in content
