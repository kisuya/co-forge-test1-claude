"""Structure tests for trending/popular stocks UI widget (trending-003)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
COMPONENTS = os.path.join(BASE, "components")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# --- Component existence ---

def test_trending_widget_component_exists():
    """TrendingWidget component should exist."""
    path = os.path.join(COMPONENTS, "TrendingWidget.tsx")
    assert os.path.isfile(path)


def test_trending_widget_is_client_component():
    """TrendingWidget must be a client component."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert '"use client"' in content


# --- Integration with dashboard ---

def test_dashboard_imports_trending_widget():
    """Dashboard page should import TrendingWidget."""
    content = _read(os.path.join(BASE, "app", "dashboard", "page.tsx"))
    assert "TrendingWidget" in content


def test_dashboard_renders_trending_widget():
    """Dashboard page should render TrendingWidget."""
    content = _read(os.path.join(BASE, "app", "dashboard", "page.tsx"))
    assert "<TrendingWidget" in content


# --- Desktop sidebar ---

def test_dashboard_sidebar_desktop():
    """Dashboard should have sidebar area for desktop."""
    content = _read(os.path.join(BASE, "app", "dashboard", "page.tsx"))
    assert 'data-testid="dashboard-sidebar"' in content
    assert "hidden md:block" in content
    assert "280" in content


def test_dashboard_mobile_trending():
    """Mobile should show trending above stockcards."""
    content = _read(os.path.join(BASE, "app", "dashboard", "page.tsx"))
    assert "md:hidden" in content


# --- Widget structure ---

def test_trending_widget_testid():
    """Should have trending-widget testid."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert 'data-testid="trending-widget"' in content


# --- Tab switching ---

def test_trending_tabs():
    """Should have trending/popular tabs."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert "트렌딩" in content
    assert "인기" in content
    assert "activeTab" in content


def test_trending_tab_role():
    """Tabs should have role=tab for accessibility."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert 'role="tab"' in content
    assert "aria-selected" in content


def test_trending_tab_testids():
    """Tabs should have testids."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert 'data-testid="tab-trending"' in content
    assert 'data-testid="tab-popular"' in content


def test_trending_tab_switching():
    """Tab click should switch between trending and popular."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert "setActiveTab" in content
    assert '"trending"' in content
    assert '"popular"' in content


# --- Trending items ---

def test_trending_list_testid():
    """Should have trending-list testid."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert 'data-testid="trending-list"' in content


def test_trending_item_testid():
    """Each item should have trending-item testid."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert 'data-testid="trending-item"' in content


def test_trending_item_name():
    """Items should show stock name."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert "stock_name" in content


def test_trending_change_pct():
    """Trending items should show change percentage with color."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert "change_pct" in content
    assert "text-red-600" in content
    assert "text-blue-600" in content
    assert 'data-testid="trending-change"' in content


def test_trending_event_count():
    """Trending items should show event count."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert "event_count" in content
    assert 'data-testid="trending-event-count"' in content


# --- Popular items ---

def test_popular_tracking_count():
    """Popular items should show tracking count."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert "tracking_count" in content
    assert 'data-testid="popular-tracking-count"' in content


def test_popular_price():
    """Popular items should show latest price."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert "latest_price" in content
    assert 'data-testid="popular-price"' in content


# --- Item navigation ---

def test_trending_item_links_to_stock():
    """Items should link to /stocks/{stock_id}."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert "/stocks/" in content
    assert "stock_id" in content


# --- Loading state ---

def test_trending_skeleton_loading():
    """Should show skeleton during loading."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert "Skeleton" in content
    assert 'data-testid="trending-skeleton"' in content


# --- Error handling ---

def test_trending_error_hidden():
    """Should hide widget on API error."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert "error" in content
    assert "return null" in content


# --- Mobile horizontal scroll ---

def test_trending_mobile_scroll():
    """Should use horizontal scroll on mobile."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert "overflow-x-auto" in content
    assert "flex-shrink-0" in content


# --- Item limit ---

def test_trending_max_10_items():
    """Should display maximum 10 items."""
    content = _read(os.path.join(COMPONENTS, "TrendingWidget.tsx"))
    assert "slice(0, 10)" in content


# --- API integration ---

def test_trending_api_exists():
    """queries.ts should have trendingApi."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "trendingApi" in content


def test_trending_api_get_trending():
    """trendingApi should have getTrending method."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "getTrending" in content
    assert "/api/trending" in content


def test_trending_api_get_popular():
    """trendingApi should have getPopular method."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "getPopular" in content
    assert "/api/popular" in content


# --- Types ---

def test_trending_types_exist():
    """types/index.ts should have TrendingStock and PopularStock types."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "TrendingStock" in content
    assert "PopularStock" in content


def test_trending_type_fields():
    """TrendingStock should have required fields."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "event_count" in content
    assert "mini_summary" in content
    assert "latest_report_id" in content


def test_popular_type_fields():
    """PopularStock should have required fields."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "tracking_count" in content
    assert "latest_change_reason" in content
