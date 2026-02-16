"""Structure tests for search debounce and auto-search (ui-004)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def test_stock_search_component_exists():
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    assert os.path.isfile(path)


def test_stock_search_has_debounce():
    """StockSearch should implement debounce (300ms)."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "DEBOUNCE_MS" in content or "debounce" in content.lower()
    assert "300" in content


def test_stock_search_has_min_query_length():
    """StockSearch should enforce minimum 2 characters."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "MIN_QUERY_LENGTH" in content
    assert "2" in content


def test_stock_search_shows_min_length_hint():
    """StockSearch should show '2글자 이상 입력하세요' hint."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "2글자 이상 입력하세요" in content


def test_stock_search_no_manual_search_button():
    """StockSearch should not have a manual search button (auto-search only)."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    # Should not have a standalone search button
    assert 'onClick={handleSearch}' not in content
    assert '>검색</button>' not in content


def test_stock_search_has_abort_controller():
    """StockSearch should use AbortController for request cancellation."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "AbortController" in content
    assert "abort" in content


def test_stock_search_has_loading_spinner():
    """StockSearch should show a spinner during loading."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "search-spinner" in content or "animate-spin" in content


def test_stock_search_has_correct_placeholder():
    """StockSearch input should have placeholder '종목명 또는 코드 검색'."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "종목명 또는 코드 검색" in content


def test_stock_search_uses_effect_for_auto_search():
    """StockSearch should use useEffect for auto-search on query change."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "useEffect" in content
    assert "useRef" in content


def test_queries_search_accepts_signal():
    """stocksApi.search should accept an AbortSignal parameter."""
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "signal" in content
    assert "AbortSignal" in content
