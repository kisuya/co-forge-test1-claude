"""Structure tests for activity history page (profile-006)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Component exists ---


def test_activity_history_component_exists():
    """ActivityHistory component should exist."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    assert os.path.exists(path), "ActivityHistory.tsx should exist"


def test_activity_history_is_client_component():
    """ActivityHistory should be a client component."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert '"use client"' in content


# --- Tab structure ---


def test_has_activity_tabs():
    """Should have tab navigation for reports and discussions."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert 'data-testid="activity-tabs"' in content


def test_has_reports_tab():
    """Should have reports tab."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert 'data-testid="tab-reports"' in content
    assert "리포트" in content


def test_has_discussions_tab():
    """Should have discussions tab."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert 'data-testid="tab-discussions"' in content
    assert "토론" in content


# --- Reports list ---


def test_has_reports_list():
    """Should have reports list container."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert 'data-testid="reports-list"' in content


def test_report_items_have_testid():
    """Report items should have data-testid."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert 'data-testid="report-item"' in content


def test_report_item_shows_stock_name():
    """Report item should show stock name."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert "stock_name" in content


def test_report_item_shows_change_pct():
    """Report item should show change percentage with color."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert "change_pct" in content
    assert "text-red-500" in content
    assert "text-blue-500" in content


def test_report_item_navigates_to_report():
    """Report item click should navigate to report detail."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert "/reports/" in content


# --- Discussions list ---


def test_has_discussions_list():
    """Should have discussions list container."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert 'data-testid="discussions-list"' in content


def test_discussion_items_have_testid():
    """Discussion items should have data-testid."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert 'data-testid="discussion-item"' in content


def test_discussion_item_navigates_to_stock():
    """Discussion item click should navigate to stock detail."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert "/stocks/" in content


# --- Empty states ---


def test_reports_empty_state():
    """Reports tab should show empty message when no reports."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert 'data-testid="empty-reports"' in content
    assert "아직 활동 이력이 없습니다" in content


def test_discussions_empty_state():
    """Discussions tab should show empty message."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert 'data-testid="empty-discussions"' in content


# --- Pagination ---


def test_reports_has_load_more():
    """Reports list should have load more button."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert 'data-testid="load-more-reports"' in content
    assert "더 보기" in content


def test_discussions_has_load_more():
    """Discussions list should have load more button."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert 'data-testid="load-more-discussions"' in content


# --- API integration ---


def test_calls_profile_reports_api():
    """Should call profileApi.getReports."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert "profileApi" in content
    assert "getReports" in content


def test_calls_profile_discussions_api():
    """Should call profileApi.getDiscussions."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert "getDiscussions" in content


def test_profile_api_has_reports_endpoint():
    """profileApi should have getReports method."""
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "getReports" in content
    assert "/api/profile/reports" in content


def test_profile_api_has_discussions_endpoint():
    """profileApi should have getDiscussions method."""
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "getDiscussions" in content
    assert "/api/profile/discussions" in content


# --- Mypage integration ---


def test_mypage_uses_activity_history():
    """Mypage should import and use ActivityHistory."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert "ActivityHistory" in content


# --- Section title ---


def test_has_section_title():
    """Should have '최근 활동' section title."""
    path = os.path.join(BASE, "components", "ActivityHistory.tsx")
    content = open(path).read()
    assert "최근 활동" in content
