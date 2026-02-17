"""Structure tests for stock detail page route (history-002)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Route exists ---


def test_stock_detail_route_exists():
    """The /stocks/[stockId] route should exist."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    assert os.path.exists(path), "stocks/[stockId]/page.tsx should exist"


def test_stock_detail_is_client_component():
    """Stock detail page should be a client component."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert '"use client"' in content


# --- Types ---


def test_stock_detail_type_exists():
    """StockDetail type should be defined."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "StockDetail" in content


def test_stock_detail_type_has_required_fields():
    """StockDetail type should have all required fields."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    for field in ["latest_price", "price_change_pct", "price_currency",
                  "price_freshness", "tracking_count", "tracking_since",
                  "is_tracked_by_me"]:
        assert field in content, f"StockDetail should have {field}"


def test_history_event_type_exists():
    """HistoryEvent type should be defined."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "HistoryEvent" in content


def test_stock_history_response_type_exists():
    """StockHistoryResponse type should be defined."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "StockHistoryResponse" in content


# --- API queries ---


def test_stocks_api_has_get_detail():
    """stocksApi should have getDetail method."""
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "getDetail" in content
    assert "/api/stocks/" in content


def test_stocks_api_has_get_history():
    """stocksApi should have getHistory method."""
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "getHistory" in content
    assert "/history" in content


# --- Page header ---


def test_page_has_stock_name():
    """Page should display stock name (24px bold)."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="stock-name"' in content
    assert "text-2xl" in content
    assert "font-bold" in content


def test_page_has_stock_code():
    """Page should display stock code (14px gray)."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="stock-code"' in content
    assert "text-gray-500" in content


def test_page_has_market_badge():
    """Page should display market badge (KRX/NYSE/NASDAQ) with colors."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="market-badge"' in content
    assert "rounded" in content
    # Market-specific badge colors
    assert "bg-blue-100" in content   # KRX
    assert "bg-green-100" in content  # NYSE
    assert "bg-purple-100" in content  # NASDAQ


def test_page_has_current_price():
    """Page should display current price and change rate."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="stock-price"' in content
    assert 'data-testid="stock-price-change"' in content


def test_page_has_tracking_count():
    """Page should display tracking count with 👥 icon."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="detail-tracking-count"' in content
    assert "👥" in content
    assert "추적 중" in content


# --- Navigation ---


def test_page_has_back_button():
    """Page should have back button to /dashboard."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="back-button"' in content
    assert "/dashboard" in content


def test_page_uses_router_params():
    """Page should use useParams to extract stockId."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert "useParams" in content
    assert "stockId" in content


# --- Not found handling ---


def test_page_handles_not_found():
    """Page should display not-found UI for nonexistent stockId."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="stock-not-found"' in content
    assert "404" in content


def test_page_not_found_has_dashboard_link():
    """Not found page should have link back to dashboard."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert "대시보드로 돌아가기" in content


# --- Auth ---


def test_page_requires_authentication():
    """Page should redirect to /login if not authenticated."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert "isLoggedIn" in content
    assert '"/login"' in content


# --- Loading state ---


def test_page_has_loading_state():
    """Page should show loading spinner while fetching data."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert "loading" in content
    assert "animate-spin" in content


# --- Error state ---


def test_page_handles_error_state():
    """Page should display error message on API failure."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="error-message"' in content
    assert "종목 정보를 불러올 수 없습니다" in content


# --- Layout ---


def test_page_has_stock_header_section():
    """Page should have stock header section."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="stock-header"' in content


def test_page_imports_event_timeline():
    """Page should import EventTimeline component."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert "EventTimeline" in content


def test_page_uses_promise_all_for_data():
    """Page should fetch stock detail and history in parallel."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert "Promise.all" in content
