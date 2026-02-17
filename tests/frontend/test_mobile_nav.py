"""Structure tests for mobile bottom navigation (ui-018)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Component exists ---


def test_mobile_nav_component_exists():
    """MobileNav component should exist."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    assert os.path.exists(path), "MobileNav.tsx should exist"


def test_mobile_nav_is_client_component():
    """MobileNav should be a client component."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert '"use client"' in content


# --- Tab bar structure ---


def test_has_mobile_nav_testid():
    """Should have data-testid for mobile nav."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert 'data-testid="mobile-nav"' in content


def test_mobile_nav_is_fixed_bottom():
    """Mobile nav should be fixed bottom."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert "fixed" in content
    assert "bottom-0" in content


def test_mobile_nav_height():
    """Mobile nav should be 56px height."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert "56px" in content


def test_mobile_nav_z50():
    """Mobile nav should have z-50."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert "z-50" in content


def test_mobile_nav_border_top():
    """Mobile nav should have border-top."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert "border-t" in content
    assert "border-gray-200" in content


def test_mobile_nav_safe_area():
    """Mobile nav should have safe-area-inset-bottom padding."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert "safe-area-inset-bottom" in content


# --- Tabs ---


def test_has_dashboard_tab():
    """Should have dashboard tab with icon."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert "대시보드" in content
    assert "🏠" in content
    assert "/dashboard" in content


def test_has_news_tab():
    """Should have news tab placeholder."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert "뉴스" in content
    assert "📰" in content


def test_has_mypage_tab():
    """Should have mypage tab."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert "마이페이지" in content
    assert "👤" in content
    assert "/mypage" in content


def test_tab_labels_10px():
    """Tab labels should be 10px."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert "10px" in content


def test_active_tab_primary_color():
    """Active tab should use primary color (blue-600)."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert "text-blue-600" in content


def test_inactive_tab_gray():
    """Inactive tab should be gray-500."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert "text-gray-500" in content


# --- Hidden on desktop ---


def test_mobile_nav_hidden_on_desktop():
    """Mobile nav should be hidden on desktop (md:hidden)."""
    path = os.path.join(BASE, "components", "MobileNav.tsx")
    content = open(path).read()
    assert "md:hidden" in content


# --- Body padding ---


def test_body_padding_bottom():
    """Body should have padding-bottom for mobile nav."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "pb-14" in content
    assert "md:pb-0" in content


# --- Layout integration ---


def test_layout_uses_mobile_nav():
    """RootLayout should import and use MobileNav."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "MobileNav" in content
