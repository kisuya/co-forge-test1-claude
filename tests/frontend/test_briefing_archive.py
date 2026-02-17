"""Structure tests for briefing archive page (briefing-005)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# --- Page existence ---

def test_briefings_page_exists():
    """Briefings archive page should exist at /briefings."""
    path = os.path.join(BASE, "app", "briefings", "page.tsx")
    assert os.path.isfile(path)


def test_briefings_page_is_client_component():
    """Briefings page must be a client component."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert '"use client"' in content


# --- Page title ---

def test_briefings_page_title():
    """Should have '마켓 브리핑' title."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert "마켓 브리핑" in content
    assert 'data-testid="briefing-archive-title"' in content


# --- Market tabs ---

def test_briefings_kr_us_tabs():
    """Should have KR/US market tabs."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert "한국" in content
    assert "미국" in content
    assert "activeMarket" in content


def test_briefings_tab_role():
    """Tabs should have role=tab for accessibility."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert 'role="tab"' in content
    assert "aria-selected" in content


def test_briefings_tab_testids():
    """Tabs should have testids."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert 'data-testid="tab-kr"' in content
    assert 'data-testid="tab-us"' in content


def test_briefings_tab_switching():
    """Tab click should change active market and refetch."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert "setActiveMarket" in content
    assert '"KR"' in content
    assert '"US"' in content


# --- Briefing list ---

def test_briefings_list_testid():
    """Should have briefing-archive-list testid."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert 'data-testid="briefing-archive-list"' in content


def test_briefings_item_testid():
    """Each briefing should have briefing-archive-item testid."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert 'data-testid="briefing-archive-item"' in content


def test_briefings_date_display():
    """Each item should show formatted date."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert 'data-testid="briefing-date"' in content
    assert "formatDate" in content


def test_briefings_date_format_with_day():
    """Date format should include day of week."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    # Korean day names
    assert "일" in content
    assert "월" in content
    assert "화" in content
    assert "수" in content
    assert "목" in content
    assert "금" in content
    assert "토" in content


def test_briefings_summary_display():
    """Each item should show summary."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert 'data-testid="briefing-archive-summary"' in content
    assert "summary" in content


# --- Collapsible key issues ---

def test_briefings_issues_collapsible():
    """Key issues should be collapsible."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert 'data-testid="briefing-archive-issues"' in content
    assert "toggleExpand" in content
    assert "expandedIds" in content


def test_briefings_issues_toggle_button():
    """Should have toggle button for key issues."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert 'data-testid="briefing-toggle-issues"' in content
    assert "aria-expanded" in content


def test_briefings_issues_content():
    """Expanded issues should show title and description."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert "key_issues" in content
    assert "title" in content
    assert "description" in content


# --- Top movers ---

def test_briefings_movers_display():
    """Should display top movers."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert 'data-testid="briefing-archive-movers"' in content
    assert "top_movers" in content


def test_briefings_movers_color():
    """Movers should have red/blue color coding."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert "text-red-600" in content
    assert "text-blue-600" in content


# --- Loading state ---

def test_briefings_skeleton_loading():
    """Should show skeleton during loading."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert "Skeleton" in content
    assert 'data-testid="briefing-archive-skeleton"' in content


# --- Empty state ---

def test_briefings_empty_state():
    """Should show empty state when no data."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert "브리핑 데이터가 없습니다" in content
    assert 'data-testid="briefing-archive-empty"' in content


# --- Data fetching ---

def test_briefings_fetches_30_days():
    """Should fetch up to 30 days of briefings."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert "30" in content
    assert "briefingsApi" in content


def test_briefings_uses_list_api():
    """Should use briefingsApi.list for data fetching."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert "briefingsApi" in content
    assert "list" in content


# --- SEO ---

def test_briefings_page_document_title():
    """Should set document title."""
    content = _read(os.path.join(BASE, "app", "briefings", "page.tsx"))
    assert "document.title" in content
    assert "oh-my-stock" in content
