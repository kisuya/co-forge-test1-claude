"""Structure tests for global error and loading UX (ui-010)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Error boundary ---

def test_error_boundary_exists():
    path = os.path.join(BASE, "app", "error.tsx")
    assert os.path.isfile(path)


def test_global_error_boundary_exists():
    path = os.path.join(BASE, "app", "global-error.tsx")
    assert os.path.isfile(path)


def test_error_boundary_has_reset_button():
    """error.tsx should have a '새로고침' reset button."""
    path = os.path.join(BASE, "app", "error.tsx")
    content = open(path).read()
    assert "새로고침" in content
    assert "error-reset-btn" in content
    assert "reset" in content


def test_error_boundary_shows_friendly_message():
    """error.tsx should show '문제가 발생했습니다'."""
    path = os.path.join(BASE, "app", "error.tsx")
    content = open(path).read()
    assert "문제가 발생했습니다" in content


def test_global_error_has_html_wrapper():
    """global-error.tsx should include html and body tags."""
    path = os.path.join(BASE, "app", "global-error.tsx")
    content = open(path).read()
    assert "<html" in content
    assert "<body" in content


# --- Toast system ---

def test_toast_utility_exists():
    path = os.path.join(BASE, "lib", "toast.ts")
    assert os.path.isfile(path)


def test_toast_has_add_remove_subscribe():
    """toast utility should export addToast, removeToast, subscribe."""
    path = os.path.join(BASE, "lib", "toast.ts")
    content = open(path).read()
    assert "addToast" in content
    assert "removeToast" in content
    assert "subscribe" in content


def test_toast_auto_dismiss_3s():
    """toast should auto-dismiss (default 3000ms)."""
    path = os.path.join(BASE, "lib", "toast.ts")
    content = open(path).read()
    assert "3000" in content


def test_toast_container_component_exists():
    path = os.path.join(BASE, "components", "ToastContainer.tsx")
    assert os.path.isfile(path)


def test_toast_container_has_red_background():
    """ToastContainer should use red background for error toasts."""
    path = os.path.join(BASE, "components", "ToastContainer.tsx")
    content = open(path).read()
    assert "bg-red-600" in content
    assert "toast-container" in content
    assert "toast-message" in content


# --- 401 auto-refresh + login redirect ---

def test_api_interceptor_handles_401_refresh():
    """api.ts should attempt token refresh on 401."""
    path = os.path.join(BASE, "lib", "api.ts")
    content = open(path).read()
    assert "401" in content
    assert "refresh" in content
    assert "/login" in content


def test_api_interceptor_shows_session_expired_toast():
    """api.ts should show toast on session expiry."""
    path = os.path.join(BASE, "lib", "api.ts")
    content = open(path).read()
    assert "addToast" in content
    assert "세션이 만료되었습니다" in content


def test_api_interceptor_shows_network_error_toast():
    """api.ts should show toast on network errors."""
    path = os.path.join(BASE, "lib", "api.ts")
    content = open(path).read()
    assert "네트워크" in content


# --- Progress bar ---

def test_progress_bar_component_exists():
    path = os.path.join(BASE, "components", "ProgressBar.tsx")
    assert os.path.isfile(path)


def test_progress_bar_tracks_pathname():
    """ProgressBar should use usePathname for navigation tracking."""
    path = os.path.join(BASE, "components", "ProgressBar.tsx")
    content = open(path).read()
    assert "usePathname" in content
    assert "progress-bar" in content


# --- Empty states ---

def test_watchlist_empty_state():
    """WatchlistManager should show '종목을 추가해보세요' empty state."""
    path = os.path.join(BASE, "components", "WatchlistManager.tsx")
    content = open(path).read()
    assert "종목을 추가해보세요" in content
    assert "empty-watchlist" in content


def test_reports_empty_state():
    """Reports page should show '아직 분석 리포트가 없습니다' empty state."""
    path = os.path.join(BASE, "app", "reports", "page.tsx")
    content = open(path).read()
    assert "아직 분석 리포트가 없습니다" in content
    assert "empty-reports" in content


# --- Layout integration ---

def test_layout_includes_toast_and_progress():
    """Root layout should include ToastContainer and ProgressBar."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "ToastContainer" in content
    assert "ProgressBar" in content


def test_globals_css_has_slide_animation():
    """globals.css should define slide-down animation for toasts."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "slide-down" in content
    assert "@keyframes" in content
