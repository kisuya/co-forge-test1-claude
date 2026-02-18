"""Structure tests for dashboard legacy header removal (fix-001).

Verifies that the dashboard page does not render a duplicate header
when the GlobalHeader in RootLayout already provides navigation,
notifications, and authentication controls.
"""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def test_dashboard_has_no_header_element():
    """Dashboard page should not contain a <header> element (GlobalHeader handles it)."""
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "<header" not in content, "Dashboard should not have its own <header> element"


def test_dashboard_no_duplicate_logo():
    """Dashboard should not render its own 'oh-my-stock' heading."""
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    # The legacy header had <h1>oh-my-stock</h1>; GlobalHeader provides the logo
    assert '<h1' not in content, "Dashboard should not have <h1> logo (GlobalHeader provides it)"


def test_dashboard_no_logout_button():
    """Dashboard should not have its own logout button (handled by profile menu)."""
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "handleLogout" not in content
    assert "clearTokens" not in content


def test_global_header_exists_in_layout():
    """RootLayout should include GlobalHeader for site-wide navigation."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "GlobalHeader" in content


def test_global_header_has_notification():
    """GlobalHeader should have notification functionality."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert "NotificationBell" in content


def test_only_one_header_in_dashboard_tree():
    """Dashboard page itself should render zero <header> tags.

    The single header comes from RootLayout's GlobalHeader.
    """
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert content.count("<header") == 0, (
        f"Expected 0 <header> tags in dashboard, found {content.count('<header')}"
    )


def test_dashboard_still_has_main_content():
    """Dashboard should still have its main content area."""
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "<main" in content
    assert "대시보드" in content
    assert "WatchlistManager" in content
