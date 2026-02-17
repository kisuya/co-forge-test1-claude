"""Structure tests for global header and desktop navigation (ui-017)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Component exists ---


def test_global_header_component_exists():
    """GlobalHeader component should exist."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    assert os.path.exists(path), "GlobalHeader.tsx should exist"


def test_global_header_is_client_component():
    """GlobalHeader should be a client component."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert '"use client"' in content


# --- Header structure ---


def test_has_global_header_testid():
    """Should have data-testid for global header."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert 'data-testid="global-header"' in content


def test_header_has_logo():
    """Header should have oh-my-stock logo."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert 'data-testid="header-logo"' in content
    assert "oh-my-stock" in content


def test_header_is_sticky():
    """Header should be sticky top-0 z-50."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert "sticky" in content
    assert "top-0" in content
    assert "z-50" in content


def test_header_height():
    """Header should be 64px height."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert "64px" in content


def test_header_border_bottom():
    """Header should have border-bottom."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert "border-b" in content
    assert "border-gray-200" in content


# --- Desktop nav ---


def test_has_desktop_nav():
    """Should have desktop nav container."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert 'data-testid="desktop-nav"' in content


def test_nav_has_dashboard_link():
    """Nav should have 대시보드 link."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert "대시보드" in content
    assert "/dashboard" in content


def test_nav_has_mypage_link():
    """Nav should have 마이페이지 link."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert "마이페이지" in content
    assert "/mypage" in content


def test_nav_active_state():
    """Active nav link should have bold and border styling."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert "font-bold" in content
    assert "border-b-2" in content


def test_nav_hidden_on_mobile():
    """Nav should be hidden on mobile (md:flex)."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert "hidden" in content
    assert "md:flex" in content


# --- Auth: logged in ---


def test_logged_in_has_profile_icon():
    """Logged-in header should have profile icon with first letter."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert 'data-testid="header-profile-icon"' in content
    assert "rounded-full" in content


def test_profile_icon_navigates_to_mypage():
    """Profile icon should navigate to /mypage."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert '"/mypage"' in content


def test_notification_bell_placeholder():
    """Should have notification bell placeholder."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert 'data-testid="notification-bell-placeholder"' in content


# --- Auth: guest ---


def test_guest_has_login_link():
    """Guest header should have 로그인 link."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert 'data-testid="header-login-link"' in content
    assert "로그인" in content


def test_guest_has_signup_button():
    """Guest header should have 시작하기 button."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert 'data-testid="header-signup-btn"' in content
    assert "시작하기" in content
    assert "/signup" in content


# --- Auth loading ---


def test_auth_loading_skeleton():
    """Should show skeleton while checking auth."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert 'data-testid="auth-skeleton"' in content
    assert "animate-pulse" in content


# --- Shared page mini header ---


def test_shared_page_no_header():
    """Shared pages should not show global header."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert "/shared" in content


# --- Uses profile API ---


def test_header_uses_profile_api():
    """Header should fetch profile for display name."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert "profileApi" in content
    assert "isLoggedIn" in content
