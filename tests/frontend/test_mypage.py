"""Structure tests for mypage route and profile card (profile-003)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Route exists ---


def test_mypage_route_exists():
    """The /mypage route should exist."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    assert os.path.exists(path), "mypage/page.tsx should exist"


def test_mypage_is_client_component():
    """Mypage should be a client component."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert '"use client"' in content


# --- Auth redirect ---


def test_mypage_requires_auth():
    """Mypage should redirect to /login if not authenticated."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert "isLoggedIn" in content
    assert '"/login"' in content


# --- Profile API ---


def test_mypage_calls_profile_api():
    """Mypage should call profileApi.get()."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert "profileApi" in content


def test_profile_api_exists_in_queries():
    """profileApi should be defined in queries.ts."""
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "profileApi" in content
    assert "/api/profile" in content


# --- Profile types ---


def test_profile_response_type_exists():
    """ProfileResponse type should be defined."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "ProfileResponse" in content


def test_profile_stats_type_exists():
    """ProfileStats type should be defined."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "ProfileStats" in content


def test_profile_response_has_required_fields():
    """ProfileResponse should have email, nickname, display_name, created_at, stats."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    for field in ["email", "nickname", "display_name", "created_at", "stats"]:
        assert field in content, f"ProfileResponse should have {field}"


# --- Profile card ---


def test_mypage_has_profile_card():
    """Mypage should have profile card."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert 'data-testid="profile-card"' in content


def test_profile_card_has_avatar():
    """Profile card should have avatar with first letter."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert 'data-testid="profile-avatar"' in content
    assert "rounded-full" in content


def test_profile_card_has_email():
    """Profile card should display email (read-only)."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert 'data-testid="profile-email"' in content
    assert "text-gray-500" in content


def test_profile_card_has_join_date():
    """Profile card should display join date."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert 'data-testid="profile-join-date"' in content
    assert "가입" in content


# --- Stats cards ---


def test_mypage_has_stats_section():
    """Mypage should have stats section."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert 'data-testid="stats-section"' in content


def test_stats_has_watchlist_count():
    """Stats should show watchlist count."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert 'data-testid="stat-watchlist"' in content
    assert "관심 종목" in content


def test_stats_has_report_count():
    """Stats should show report count."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert 'data-testid="stat-reports"' in content
    assert "받은 리포트" in content


def test_stats_has_discussion_count():
    """Stats should show discussion count."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert 'data-testid="stat-discussions"' in content
    assert "작성 토론" in content


def test_stats_cards_bold_numbers():
    """Stats numbers should be 24px bold."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert "text-2xl" in content
    assert "font-bold" in content


def test_stats_cards_responsive():
    """Stats cards should stack vertically on mobile."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert "grid-cols-1" in content
    assert "sm:grid-cols-3" in content


# --- Error handling ---


def test_mypage_has_error_state():
    """Mypage should show error message on API failure."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert 'data-testid="mypage-error"' in content
    assert "프로필을 불러올 수 없습니다" in content


def test_mypage_has_retry_button():
    """Mypage error state should have retry button."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert 'data-testid="retry-button"' in content
    assert "다시 시도" in content


# --- Loading state ---


def test_mypage_has_loading_skeleton():
    """Mypage should show skeleton while loading."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert 'data-testid="mypage-skeleton"' in content
    assert "animate-pulse" in content


# --- Page title ---


def test_mypage_has_title():
    """Mypage should have '마이페이지' title."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert "마이페이지" in content
