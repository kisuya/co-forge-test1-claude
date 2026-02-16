"""Structure tests for similar case UI (ui-009)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- SimilarCases component ---


def test_similar_cases_component_exists():
    path = os.path.join(BASE, "components", "SimilarCases.tsx")
    assert os.path.isfile(path)


def test_similar_cases_has_toggle():
    """Should have collapsible toggle for the section."""
    path = os.path.join(BASE, "components", "SimilarCases.tsx")
    content = open(path).read()
    assert "similar-cases-toggle" in content
    assert "open" in content


def test_similar_cases_fetches_api():
    """Should call casesApi.getByReport."""
    path = os.path.join(BASE, "components", "SimilarCases.tsx")
    content = open(path).read()
    assert "casesApi" in content
    assert "getByReport" in content


def test_similar_cases_empty_state():
    """Should show empty message when no cases."""
    path = os.path.join(BASE, "components", "SimilarCases.tsx")
    content = open(path).read()
    assert "similar-cases-empty" in content
    assert "유사한 과거 변동 사례가 아직 충분하지 않습니다" in content
    assert "데이터가 쌓이면 자동으로 표시됩니다" in content


def test_similar_cases_card():
    """Should render case cards with date, change_pct, similarity badge."""
    path = os.path.join(BASE, "components", "SimilarCases.tsx")
    content = open(path).read()
    assert "similar-case-card" in content
    assert "유사도" in content


def test_similar_cases_change_colors():
    """Should use red for positive and blue for negative changes."""
    path = os.path.join(BASE, "components", "SimilarCases.tsx")
    content = open(path).read()
    assert "text-red-600" in content
    assert "text-blue-600" in content


def test_similar_cases_trend_display():
    """Should show 1w and 1m trend summaries."""
    path = os.path.join(BASE, "components", "SimilarCases.tsx")
    content = open(path).read()
    assert "1주 후" in content
    assert "1개월 후" in content


def test_similar_cases_similarity_badges():
    """Should show 높음/중간/낮음 badges based on score."""
    path = os.path.join(BASE, "components", "SimilarCases.tsx")
    content = open(path).read()
    assert "높음" in content
    assert "중간" in content
    assert "낮음" in content


def test_similar_cases_data_insufficient():
    """Should show insufficient data message when flagged."""
    path = os.path.join(BASE, "components", "SimilarCases.tsx")
    content = open(path).read()
    assert "data_insufficient" in content
    assert "추이 데이터 부족" in content


def test_similar_cases_mobile_stack():
    """Cards should use grid-cols-1 for mobile vertical stack."""
    path = os.path.join(BASE, "components", "SimilarCases.tsx")
    content = open(path).read()
    assert "grid-cols-1" in content


# --- ReportView integration ---


def test_report_view_includes_similar_cases():
    """ReportView should import and render SimilarCases."""
    path = os.path.join(BASE, "components", "ReportView.tsx")
    content = open(path).read()
    assert "SimilarCases" in content
    assert "reportId" in content


# --- Types ---


def test_types_has_similar_case_types():
    """types/index.ts should include SimilarCaseItem and CasesResponse."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "SimilarCaseItem" in content
    assert "CasesResponse" in content
    assert "TrendPoint" in content


# --- Queries ---


def test_queries_has_cases_api():
    """queries.ts should have casesApi.getByReport."""
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "casesApi" in content
    assert "/api/cases/" in content
