"""Structure tests for news feed page UI (news-004)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# --- Page existence ---

def test_news_page_exists():
    """News feed page should exist at /news."""
    path = os.path.join(BASE, "app", "news", "page.tsx")
    assert os.path.isfile(path)


def test_news_page_is_client_component():
    """News feed page must be a client component."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert '"use client"' in content


# --- Page title ---

def test_news_page_title():
    """Should have '📰 뉴스 피드' title."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert "뉴스 피드" in content
    assert 'data-testid="news-feed-title"' in content


# --- Filters ---

def test_news_stock_filter():
    """Should have stock filter dropdown."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert 'data-testid="news-stock-filter"' in content
    assert "전체 종목" in content
    assert "stockFilter" in content


def test_news_importance_filter():
    """Should have importance filter dropdown."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert 'data-testid="news-importance-filter"' in content
    assert "전체 중요도" in content
    assert "importanceFilter" in content


def test_news_importance_options():
    """Should have high/medium/low filter options."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert "높음" in content
    assert "보통" in content
    assert "낮음" in content


def test_news_filters_container():
    """Filters should be grouped."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert 'data-testid="news-filters"' in content


# --- News list ---

def test_news_list_testid():
    """Should have news-list testid."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert 'data-testid="news-list"' in content


def test_news_item_testid():
    """Each news item should have testid."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert 'data-testid="news-item"' in content


def test_news_item_stock_tag():
    """News item should show stock name tag."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert 'data-testid="news-stock-tag"' in content
    assert "stock_name" in content


def test_news_item_summary():
    """News item should show AI summary."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert 'data-testid="news-summary"' in content
    assert "summary" in content


def test_news_item_title():
    """News item should show original title."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert 'data-testid="news-title"' in content
    assert "title" in content


def test_news_item_source_and_time():
    """News item should show source and relative time."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert 'data-testid="news-source"' in content
    assert 'data-testid="news-time"' in content
    assert "relativeTime" in content


def test_news_item_importance_badge():
    """News item should show importance badge."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert 'data-testid="news-importance-badge"' in content
    assert "importanceBadge" in content


def test_news_importance_badge_colors():
    """Importance badge should have correct colors."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert "bg-red-100" in content
    assert "bg-yellow-100" in content
    assert "bg-gray-100" in content


def test_news_item_opens_new_tab():
    """Clicking news item should open in new tab."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert 'target="_blank"' in content
    assert 'rel="noopener noreferrer"' in content


# --- Infinite scroll ---

def test_news_infinite_scroll():
    """Should use Intersection Observer for infinite scroll."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert "IntersectionObserver" in content
    assert "observerRef" in content
    assert 'data-testid="news-scroll-sentinel"' in content


def test_news_loading_more():
    """Should show loading indicator when fetching more."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert "loadingMore" in content
    assert 'data-testid="news-loading-more"' in content


# --- Empty state ---

def test_news_empty_state():
    """Should show empty state when no news."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert "관심 종목의 뉴스가 없습니다" in content
    assert "종목을 추가해보세요" in content
    assert 'data-testid="news-empty"' in content


# --- Loading state ---

def test_news_skeleton_loading():
    """Should show skeleton during initial loading."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert "Skeleton" in content
    assert 'data-testid="news-skeleton"' in content


# --- Mobile nav connection ---

def test_mobile_nav_links_to_news():
    """Mobile nav should link to /news."""
    content = _read(os.path.join(BASE, "components", "MobileNav.tsx"))
    assert "/news" in content
    assert "뉴스" in content


# --- API integration ---

def test_news_api_exists():
    """queries.ts should have newsApi."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "newsApi" in content


def test_news_api_list_method():
    """newsApi should have list method."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "/api/news" in content


# --- Types ---

def test_news_types_exist():
    """types/index.ts should have NewsItem and NewsFeedResponse types."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "NewsItem" in content
    assert "NewsFeedResponse" in content


def test_news_type_fields():
    """NewsItem should have required fields."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "stock_name" in content
    assert "importance" in content
    assert "published_at" in content


# --- Auth redirect ---

def test_news_requires_auth():
    """News page should redirect unauthenticated users."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert "isLoggedIn" in content
    assert "/login" in content


# --- SEO ---

def test_news_page_document_title():
    """Should set document title."""
    content = _read(os.path.join(BASE, "app", "news", "page.tsx"))
    assert "document.title" in content
    assert "oh-my-stock" in content
