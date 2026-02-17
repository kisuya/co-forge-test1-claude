"""Structure tests for stock add toast and history entry points (history-005)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Stock add toast ---


def test_watchlist_manager_imports_toast():
    """WatchlistManager should import addToast."""
    path = os.path.join(BASE, "components", "WatchlistManager.tsx")
    content = open(path).read()
    assert "addToast" in content


def test_watchlist_add_success_toast():
    """Adding a stock should show success toast."""
    path = os.path.join(BASE, "components", "WatchlistManager.tsx")
    content = open(path).read()
    assert "종목 추적이 시작되었습니다" in content
    assert '"success"' in content


def test_watchlist_add_failure_toast():
    """Failed stock add should show error toast."""
    path = os.path.join(BASE, "components", "WatchlistManager.tsx")
    content = open(path).read()
    assert "종목 추가에 실패했습니다" in content
    assert '"error"' in content


# --- StockCard stock name click → /stocks/{stock_id} ---


def test_stockcard_name_is_clickable():
    """StockCard stock name should be clickable."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="stock-name-link"' in content
    assert "cursor-pointer" in content


def test_stockcard_name_has_hover_underline():
    """StockCard stock name should have hover underline."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "hover:underline" in content


def test_stockcard_name_navigates_to_stock_detail():
    """StockCard stock name click should navigate to /stocks/{stock_id}."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "/stocks/" in content
    assert "stock_id" in content


def test_stockcard_name_stops_propagation():
    """StockCard stock name click should stop event propagation."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    # Stock name link area should have stopPropagation
    assert "stopPropagation" in content


# --- ⋮ menu history → /stocks/{stock_id} ---


def test_kebab_menu_history_navigates():
    """Kebab menu '이벤트 히스토리' should navigate to /stocks/{stock_id}."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "이벤트 히스토리" in content
    # Should link to stocks page
    assert "router.push(`/stocks/${item.stock_id}`)" in content


# --- Report page stock name click → /stocks/{stock_id} ---


def test_report_view_stock_name_is_clickable():
    """ReportView stock name should be clickable."""
    path = os.path.join(BASE, "components", "ReportView.tsx")
    content = open(path).read()
    assert 'data-testid="report-stock-link"' in content
    assert "cursor-pointer" in content


def test_report_view_stock_name_has_hover_underline():
    """ReportView stock name should have hover underline."""
    path = os.path.join(BASE, "components", "ReportView.tsx")
    content = open(path).read()
    assert "hover:underline" in content


def test_report_view_stock_name_navigates_to_stock_detail():
    """ReportView stock name click should navigate to /stocks/{stock_id}."""
    path = os.path.join(BASE, "components", "ReportView.tsx")
    content = open(path).read()
    assert "/stocks/" in content
    assert "stock_id" in content


def test_report_view_uses_router():
    """ReportView should use useRouter for navigation."""
    path = os.path.join(BASE, "components", "ReportView.tsx")
    content = open(path).read()
    assert "useRouter" in content
    assert "router.push" in content


# --- 404 fallback ---


def test_stock_detail_page_handles_404():
    """Stock detail page should handle 404 for nonexistent stock_id."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert "404" in content
    assert "notFound" in content
    assert "종목을 찾을 수 없습니다" in content
