"""Structure tests for dashboard news summary widget (news-005)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
COMPONENTS = os.path.join(BASE, "components")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# --- Component existence ---

def test_news_widget_component_exists():
    """NewsWidget component should exist."""
    path = os.path.join(COMPONENTS, "NewsWidget.tsx")
    assert os.path.isfile(path)


def test_news_widget_is_client_component():
    """NewsWidget must be a client component."""
    content = _read(os.path.join(COMPONENTS, "NewsWidget.tsx"))
    assert '"use client"' in content


# --- Integration with dashboard ---

def test_dashboard_imports_news_widget():
    """Dashboard page should import NewsWidget."""
    content = _read(os.path.join(BASE, "app", "dashboard", "page.tsx"))
    assert "NewsWidget" in content


def test_dashboard_renders_news_widget():
    """Dashboard page should render NewsWidget."""
    content = _read(os.path.join(BASE, "app", "dashboard", "page.tsx"))
    assert "<NewsWidget" in content


# --- Widget structure ---

def test_news_widget_testid():
    """Should have news-widget testid."""
    content = _read(os.path.join(COMPONENTS, "NewsWidget.tsx"))
    assert 'data-testid="news-widget"' in content


def test_news_widget_title():
    """Should show '📰 관심 종목 뉴스' title."""
    content = _read(os.path.join(COMPONENTS, "NewsWidget.tsx"))
    assert "관심 종목 뉴스" in content


# --- Widget items ---

def test_news_widget_list():
    """Should have news-widget-list testid."""
    content = _read(os.path.join(COMPONENTS, "NewsWidget.tsx"))
    assert 'data-testid="news-widget-list"' in content


def test_news_widget_item():
    """Each item should have news-widget-item testid."""
    content = _read(os.path.join(COMPONENTS, "NewsWidget.tsx"))
    assert 'data-testid="news-widget-item"' in content


def test_news_widget_stock_tag():
    """Items should show stock name tag."""
    content = _read(os.path.join(COMPONENTS, "NewsWidget.tsx"))
    assert 'data-testid="news-widget-stock-tag"' in content
    assert "stock_name" in content


def test_news_widget_summary():
    """Items should show summary text."""
    content = _read(os.path.join(COMPONENTS, "NewsWidget.tsx"))
    assert "summary" in content
    assert "title" in content


def test_news_widget_time():
    """Items should show relative time."""
    content = _read(os.path.join(COMPONENTS, "NewsWidget.tsx"))
    assert "relativeTime" in content
    assert "published_at" in content


# --- Link to full news page ---

def test_news_widget_full_link():
    """Should have '전체 뉴스 보기' link to /news."""
    content = _read(os.path.join(COMPONENTS, "NewsWidget.tsx"))
    assert "전체 뉴스 보기" in content
    assert "/news" in content
    assert 'data-testid="news-widget-link"' in content


# --- API call ---

def test_news_widget_fetches_high_importance():
    """Should fetch importance=high news only."""
    content = _read(os.path.join(COMPONENTS, "NewsWidget.tsx"))
    assert "high" in content
    assert "newsApi" in content


def test_news_widget_limit_5():
    """Should limit to 5 items."""
    content = _read(os.path.join(COMPONENTS, "NewsWidget.tsx"))
    assert "5" in content
    assert "per_page" in content


# --- Empty state ---

def test_news_widget_hidden_when_empty():
    """Should return null when no news items."""
    content = _read(os.path.join(COMPONENTS, "NewsWidget.tsx"))
    assert "return null" in content


# --- External links ---

def test_news_widget_opens_new_tab():
    """News links should open in new tab."""
    content = _read(os.path.join(COMPONENTS, "NewsWidget.tsx"))
    assert 'target="_blank"' in content
    assert 'rel="noopener noreferrer"' in content
