"""Structure tests for dashboard briefing card (briefing-004)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
COMPONENTS = os.path.join(BASE, "components")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# --- Component existence ---

def test_briefing_card_component_exists():
    """BriefingCard component should exist."""
    path = os.path.join(COMPONENTS, "BriefingCard.tsx")
    assert os.path.isfile(path)


def test_briefing_card_is_client_component():
    """BriefingCard must be a client component."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert '"use client"' in content


# --- Integration with dashboard ---

def test_dashboard_imports_briefing_card():
    """Dashboard page should import BriefingCard."""
    content = _read(os.path.join(BASE, "app", "dashboard", "page.tsx"))
    assert "BriefingCard" in content


def test_dashboard_renders_briefing_card():
    """Dashboard page should render BriefingCard."""
    content = _read(os.path.join(BASE, "app", "dashboard", "page.tsx"))
    assert "<BriefingCard" in content


# --- Card structure ---

def test_briefing_card_testid():
    """Should have briefing-card testid."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert 'data-testid="briefing-card"' in content


def test_briefing_card_title():
    """Should show '📈 오늘의 시장' title."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "오늘의 시장" in content


def test_briefing_card_date():
    """Should display the briefing date."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "date" in content
    assert "formatDate" in content


# --- Summary ---

def test_briefing_card_summary_testid():
    """Should have briefing-summary testid."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert 'data-testid="briefing-summary"' in content


def test_briefing_card_summary_line_clamp():
    """Summary should be limited to 2 lines."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "line-clamp-2" in content


# --- Key issues ---

def test_briefing_card_issues_testid():
    """Should have briefing-issues testid."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert 'data-testid="briefing-issues"' in content


def test_briefing_card_issues_heading():
    """Should show '주요 이슈' heading."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "주요 이슈" in content


def test_briefing_card_issues_bullet():
    """Key issues should show bullet points."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "key_issues" in content
    # Limited to 3 items
    assert "slice(0, 3)" in content


# --- Top movers ---

def test_briefing_card_movers_testid():
    """Should have briefing-movers testid."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert 'data-testid="briefing-movers"' in content


def test_briefing_card_movers_heading():
    """Should show '특징주' heading."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "특징주" in content


def test_briefing_card_movers_color():
    """Top movers should have red/blue color coding."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "text-red-600" in content
    assert "text-blue-600" in content


def test_briefing_card_movers_limit():
    """Top movers limited to 3 items."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "top_movers" in content
    assert "change_pct" in content


def test_briefing_card_movers_arrows():
    """Should show up/down arrows for movers."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "▲" in content
    assert "▼" in content


# --- Market tabs ---

def test_briefing_card_kr_us_tabs():
    """Should have KR/US market tabs."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "한국" in content
    assert "미국" in content
    assert "activeMarket" in content


def test_briefing_card_tab_role():
    """Tabs should have role=tab for accessibility."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert 'role="tab"' in content
    assert "aria-selected" in content


def test_briefing_card_tab_switching():
    """Tab click should change active market."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "setActiveMarket" in content
    assert '"KR"' in content
    assert '"US"' in content


# --- Link to archive ---

def test_briefing_card_archive_link():
    """Should have '전체 보기' link to /briefings."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "전체 보기" in content
    assert "/briefings" in content
    assert 'data-testid="briefing-link"' in content


# --- Empty/loading state ---

def test_briefing_card_skeleton_loading():
    """Should show skeleton during loading."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "Skeleton" in content
    assert 'data-testid="briefing-skeleton"' in content


def test_briefing_card_hidden_when_no_data():
    """Should return null when no briefing data."""
    content = _read(os.path.join(COMPONENTS, "BriefingCard.tsx"))
    assert "return null" in content


# --- API integration ---

def test_briefings_api_exists():
    """queries.ts should have briefingsApi."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "briefingsApi" in content


def test_briefings_api_get_today():
    """briefingsApi should have getToday method."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "getToday" in content
    assert "/api/briefings/today" in content


def test_briefings_api_list():
    """briefingsApi should have list method with market and limit params."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "list" in content
    assert "/api/briefings" in content
    assert "market" in content
    assert "limit" in content


# --- Types ---

def test_briefing_types_exist():
    """types/index.ts should have BriefingResponse types."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "BriefingResponse" in content
    assert "BriefingTodayResponse" in content


def test_briefing_type_fields():
    """BriefingResponse should have required fields."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "BriefingKeyIssue" in content
    assert "BriefingTopMover" in content
    assert "summary" in content
    assert "key_issues" in content
    assert "top_movers" in content


def test_briefing_today_type_fields():
    """BriefingTodayResponse should have is_today field."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "is_today" in content
