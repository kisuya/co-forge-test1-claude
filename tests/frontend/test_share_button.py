"""Structure tests for report share button and clipboard UI (share-004)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Share button exists ---


def test_share_button_exists():
    """Report detail page should have a share button."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="share-button"' in content


def test_share_button_has_icon_and_text():
    """Share button should show 🔗 icon and '공유' text."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert "🔗" in content
    assert "공유" in content


def test_share_button_calls_share_api():
    """Share button should call shareApi.create on click."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert "shareApi" in content
    assert "handleShare" in content


def test_share_imports_share_api():
    """Page should import shareApi from queries."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert "shareApi" in content
    assert "from" in content


# --- Clipboard copy ---


def test_share_uses_clipboard_api():
    """Share should use navigator.clipboard.writeText."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert "navigator.clipboard" in content
    assert "writeText" in content


def test_share_success_toast():
    """Share success should show green toast with expiry info."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert "공유 링크가 복사되었습니다 (30일간 유효)" in content
    assert '"success"' in content


def test_share_uses_toast():
    """Page should import addToast."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert "addToast" in content


# --- Clipboard fallback ---


def test_share_has_clipboard_fallback():
    """Share should have fallback modal when clipboard API unavailable."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="clipboard-fallback-modal"' in content


def test_fallback_has_readonly_input():
    """Fallback modal should have readonly input with share URL."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="fallback-url-input"' in content
    assert "readOnly" in content


def test_fallback_has_copy_button():
    """Fallback modal should have copy button."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="fallback-copy-button"' in content
    assert "복사" in content


# --- Error handling ---


def test_share_error_403_toast():
    """Share should show error toast on 403 (not tracked stock)."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert "403" in content
    assert "본인의 추적 종목 리포트만 공유할 수 있습니다" in content


def test_share_generic_error_toast():
    """Share should show generic error toast on other failures."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert "공유 링크 생성에 실패했습니다" in content


# --- Loading state ---


def test_share_button_has_loading_state():
    """Share button should show spinner while loading."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert "sharing" in content
    assert "animate-spin" in content
    assert 'data-testid="share-spinner"' in content


def test_share_button_disabled_during_loading():
    """Share button should be disabled during loading."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert "disabled={sharing}" in content
    assert "disabled:opacity" in content
