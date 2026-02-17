"""Structure tests for trending full page UI (trending-004)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# --- Page existence ---

def test_trending_page_exists():
    """Trending page should exist at /trending."""
    path = os.path.join(BASE, "app", "trending", "page.tsx")
    assert os.path.isfile(path)


def test_trending_page_is_client_component():
    """Trending page must be a client component."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert '"use client"' in content


# --- Page title ---

def test_trending_page_title():
    """Should have page title with testid."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "트렌딩 종목" in content
    assert 'data-testid="trending-page-title"' in content


def test_trending_page_document_title():
    """Should set document title."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "document.title" in content
    assert "oh-my-stock" in content


# --- Filters ---

def test_trending_filters_container():
    """Should have filters container."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'data-testid="trending-filters"' in content


def test_trending_market_filter():
    """Should have market filter tabs."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "marketFilter" in content
    assert "setMarketFilter" in content
    assert "filter-market-" in content
    assert '"ALL"' in content
    assert '"KR"' in content
    assert '"US"' in content


def test_trending_market_labels():
    """Market filter should show Korean labels."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "전체" in content
    assert "한국" in content
    assert "미국" in content


def test_trending_period_filter():
    """Should have period filter tabs."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "periodFilter" in content
    assert "setPeriodFilter" in content
    assert 'data-testid="filter-period-daily"' in content
    assert 'data-testid="filter-period-weekly"' in content


def test_trending_period_labels():
    """Period filter should show Korean labels."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "일간" in content
    assert "주간" in content


def test_trending_filter_accessibility():
    """Filter tabs should have proper accessibility attributes."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'role="tab"' in content
    assert "aria-selected" in content
    assert 'role="tablist"' in content


# --- Trending section ---

def test_trending_section():
    """Should have trending section."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'data-testid="trending-section"' in content
    assert "급변동 종목" in content


def test_trending_page_list():
    """Should have trending list."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'data-testid="trending-page-list"' in content


def test_trending_page_item():
    """Each item should have testid."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'data-testid="trending-page-item"' in content


def test_trending_item_name():
    """Items should show stock name."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "stock_name" in content


def test_trending_item_change_pct():
    """Items should show change percentage with color coding."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "change_pct" in content
    assert "text-red-600" in content
    assert "text-blue-600" in content


def test_trending_market_badge():
    """Items should show market badge."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'data-testid="trending-market-badge"' in content
    assert "market" in content


def test_trending_mini_summary():
    """Items should show mini summary when available."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "mini_summary" in content


def test_trending_item_links():
    """Items should link to stock detail page."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "/stocks/" in content
    assert "stock_id" in content


# --- Popular section ---

def test_popular_section():
    """Should have popular section."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'data-testid="popular-section"' in content
    assert "인기 종목" in content


def test_popular_page_list():
    """Should have popular list."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'data-testid="popular-page-list"' in content


def test_popular_page_item():
    """Each popular item should have testid."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'data-testid="popular-page-item"' in content


def test_popular_rank():
    """Popular items should show rank number."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'data-testid="popular-rank"' in content
    assert "idx + 1" in content


def test_popular_tracking_count():
    """Popular items should show tracking count."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "tracking_count" in content


def test_popular_price():
    """Popular items should show latest price."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "latest_price" in content
    assert "toLocaleString" in content


# --- Empty states ---

def test_trending_no_data():
    """Should show empty state for trending."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'data-testid="trending-no-data"' in content
    assert "아직 트렌딩 데이터가 없습니다" in content


def test_popular_no_data():
    """Should show empty state for popular."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "인기 종목 데이터가 없습니다" in content


# --- Loading state ---

def test_trending_page_skeleton():
    """Should show skeleton during loading."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "Skeleton" in content
    assert 'data-testid="trending-page-skeleton"' in content


# --- Error state ---

def test_trending_error_state():
    """Should show error state."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'data-testid="trending-error"' in content
    assert "데이터를 불러올 수 없습니다" in content


def test_trending_retry_button():
    """Should have retry button."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'data-testid="trending-retry"' in content
    assert "다시 시도" in content


# --- CTA banner ---

def test_trending_cta_banner():
    """Should show CTA for non-logged-in users."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert 'data-testid="trending-cta"' in content
    assert "종목을 추적하려면 가입하세요" in content
    assert "무료로 시작하기" in content
    assert "/signup" in content


def test_trending_cta_auth_check():
    """Should check login status for CTA."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "isLoggedIn" in content
    assert "loggedIn" in content


# --- API integration ---

def test_trending_page_uses_api():
    """Should use trendingApi."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "trendingApi" in content
    assert "getTrending" in content
    assert "getPopular" in content


def test_trending_page_passes_filters():
    """Should pass market and period filters to API."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "marketFilter" in content
    assert "periodFilter" in content
    assert "getTrending(marketFilter, periodFilter)" in content
    assert "getPopular(marketFilter)" in content


# --- Types ---

def test_trending_page_uses_types():
    """Should use TrendingStock and PopularStock types."""
    content = _read(os.path.join(BASE, "app", "trending", "page.tsx"))
    assert "TrendingStock" in content
    assert "PopularStock" in content
