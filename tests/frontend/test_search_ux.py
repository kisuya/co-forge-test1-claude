"""Structure tests for search result UX improvements (ui-005)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def test_highlight_utility_exists():
    path = os.path.join(BASE, "lib", "highlight.ts")
    assert os.path.isfile(path)


def test_highlight_has_highlight_match_function():
    path = os.path.join(BASE, "lib", "highlight.ts")
    content = open(path).read()
    assert "highlightMatch" in content
    assert "HighlightPart" in content


def test_stock_search_uses_highlight():
    """StockSearch should import and use highlightMatch."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "highlightMatch" in content
    assert "highlight" in content


def test_stock_search_highlights_name_and_code():
    """StockSearch should highlight both stock name and code."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "nameParts" in content
    assert "codeParts" in content
    assert "<strong" in content


def test_stock_search_no_results_message():
    """StockSearch should show '검색 결과가 없습니다' on empty results."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "검색 결과가 없습니다" in content
    assert "종목코드를 직접 입력" in content


def test_stock_search_check_animation():
    """StockSearch should show check animation on add."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "check-animation" in content
    assert "addedId" in content


def test_stock_search_auto_close_after_add():
    """StockSearch should auto-close results after adding a stock."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "ADD_CLOSE_DELAY_MS" in content or "500" in content
    assert "setShowResults(false)" in content


def test_stock_search_close_on_escape():
    """StockSearch should close results on Escape key."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "Escape" in content


def test_stock_search_close_on_outside_click():
    """StockSearch should close results on outside click."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "mousedown" in content
    assert "containerRef" in content


def test_stock_search_already_added_badge():
    """StockSearch should show '추가됨' badge for existing stocks."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "already-added-badge" in content
    assert "추가됨" in content
