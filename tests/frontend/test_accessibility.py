"""Structure tests for accessibility improvements (ui-030)."""
import os
import re

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
COMPONENTS = os.path.join(BASE, "components")
APP = os.path.join(BASE, "app")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


def _count_aria_labels_in_dir(directory: str) -> int:
    """Count aria-label occurrences across all tsx files in directory."""
    count = 0
    for root, _, files in os.walk(directory):
        for fname in files:
            if fname.endswith(".tsx"):
                content = _read(os.path.join(root, fname))
                count += content.count("aria-label")
    return count


# === aria-label tests (minimum 20) ===

def test_aria_label_count_minimum():
    """Should have at least 20 aria-label attributes across components."""
    total = _count_aria_labels_in_dir(BASE)
    assert total >= 20, f"Expected at least 20 aria-labels, found {total}"


def test_password_toggle_visibility_aria():
    """Password visibility toggle buttons should have aria-labels."""
    content = _read(os.path.join(COMPONENTS, "PasswordChangeForm.tsx"))
    assert content.count("aria-label") >= 3, "3 eye icon buttons should have aria-label"
    assert "비밀번호 표시 토글" in content


def test_notification_close_aria():
    """Notification close button should have aria-label."""
    content = _read(os.path.join(COMPONENTS, "NotificationPanel.tsx"))
    assert "알림 패널 닫기" in content


def test_notification_bell_aria():
    """Notification bell should have aria-label."""
    content = _read(os.path.join(COMPONENTS, "NotificationBell.tsx"))
    assert 'aria-label="알림"' in content


def test_kebab_menu_aria():
    """Kebab menu button should have aria-label."""
    content = _read(os.path.join(COMPONENTS, "StockCard.tsx"))
    assert "종목 관리 메뉴" in content


def test_threshold_buttons_aria():
    """Threshold +/- buttons should have aria-labels."""
    content = _read(os.path.join(COMPONENTS, "StockCard.tsx"))
    assert "임계값 감소" in content
    assert "임계값 증가" in content


def test_profile_icon_aria():
    """Profile icon button should have aria-label."""
    content = _read(os.path.join(COMPONENTS, "GlobalHeader.tsx"))
    assert "마이페이지" in content


def test_search_input_aria():
    """Search input should have aria-label."""
    content = _read(os.path.join(COMPONENTS, "StockSearch.tsx"))
    assert 'aria-label="종목 검색"' in content


def test_recent_search_remove_aria():
    """Recent search remove button should have aria-label."""
    content = _read(os.path.join(COMPONENTS, "RecentSearches.tsx"))
    assert "최근 검색어 삭제" in content


def test_toast_close_aria():
    """Toast close button should have aria-label."""
    content = _read(os.path.join(COMPONENTS, "ToastContainer.tsx"))
    assert 'aria-label="닫기"' in content


def test_nickname_edit_aria():
    """Nickname edit button should have aria-label."""
    content = _read(os.path.join(COMPONENTS, "NicknameEditor.tsx"))
    assert "닉네임 수정" in content


# === role="dialog" / role="menu" tests ===

def test_dialog_role_confirm_delete():
    """Confirm delete dialog should have role=dialog."""
    content = _read(os.path.join(COMPONENTS, "StockCard.tsx"))
    assert 'role="dialog"' in content


def test_dialog_role_notification_panel():
    """Notification panel should have role=dialog."""
    content = _read(os.path.join(COMPONENTS, "NotificationPanel.tsx"))
    assert 'role="dialog"' in content


def test_dialog_role_onboarding():
    """Onboarding modals should have role=dialog."""
    content = _read(os.path.join(COMPONENTS, "OnboardingOverlay.tsx"))
    assert content.count('role="dialog"') >= 3


def test_menu_role_kebab():
    """Kebab dropdown should have role=menu."""
    content = _read(os.path.join(COMPONENTS, "StockCard.tsx"))
    assert 'role="menu"' in content


def test_menu_items():
    """Menu items should have role=menuitem."""
    content = _read(os.path.join(COMPONENTS, "StockCard.tsx"))
    assert content.count('role="menuitem"') >= 3


# === aria-expanded / aria-haspopup ===

def test_kebab_aria_expanded():
    """Kebab menu should have aria-expanded."""
    content = _read(os.path.join(COMPONENTS, "StockCard.tsx"))
    assert "aria-expanded" in content


def test_kebab_aria_haspopup():
    """Kebab menu should have aria-haspopup."""
    content = _read(os.path.join(COMPONENTS, "StockCard.tsx"))
    assert "aria-haspopup" in content


def test_notification_bell_aria_expanded():
    """Notification bell should have aria-expanded."""
    content = _read(os.path.join(COMPONENTS, "NotificationBell.tsx"))
    assert "aria-expanded" in content


def test_password_toggle_aria_expanded():
    """Password toggle should have aria-expanded."""
    content = _read(os.path.join(COMPONENTS, "PasswordChangeForm.tsx"))
    assert "aria-expanded" in content


# === Form aria-describedby ===

def test_login_form_aria_describedby():
    """Login form inputs should use aria-describedby for error linking."""
    content = _read(os.path.join(APP, "login", "page.tsx"))
    assert "aria-describedby" in content


def test_signup_form_aria_describedby():
    """Signup form inputs should use aria-describedby for error linking."""
    content = _read(os.path.join(APP, "signup", "page.tsx"))
    assert "aria-describedby" in content


def test_password_form_aria_describedby():
    """Password form input should use aria-describedby for error linking."""
    content = _read(os.path.join(COMPONENTS, "PasswordChangeForm.tsx"))
    assert "aria-describedby" in content


# === Tab navigation / focus ===

def test_focus_visible_style():
    """Global CSS should have focus-visible outline style."""
    css = _read(os.path.join(APP, "globals.css"))
    assert "focus-visible" in css
    assert "outline" in css
    assert "var(--color-primary)" in css


# === Skip to main content ===

def test_skip_to_main_link():
    """Layout should have skip to main content link."""
    content = _read(os.path.join(APP, "layout.tsx"))
    assert "skip-to-main" in content
    assert "본문으로 건너뛰기" in content


def test_main_content_id():
    """Layout should have main-content id target."""
    content = _read(os.path.join(APP, "layout.tsx"))
    assert 'id="main-content"' in content


def test_skip_link_sr_only():
    """Skip link should be sr-only by default."""
    content = _read(os.path.join(APP, "layout.tsx"))
    assert "sr-only" in content


# === Color contrast ===

def test_body_text_contrast():
    """Body text should use gray-900 for WCAG AA contrast."""
    content = _read(os.path.join(APP, "layout.tsx"))
    assert "text-gray-900" in content


# === Navigation labels ===

def test_desktop_nav_aria_label():
    """Desktop nav should have aria-label."""
    content = _read(os.path.join(COMPONENTS, "GlobalHeader.tsx"))
    assert "메인 내비게이션" in content


def test_mobile_nav_aria_label():
    """Mobile nav should have aria-label."""
    content = _read(os.path.join(COMPONENTS, "MobileNav.tsx"))
    assert "모바일 내비게이션" in content


# === Tab roles ===

def test_activity_tabs_role():
    """Activity history tabs should have role=tablist."""
    content = _read(os.path.join(COMPONENTS, "ActivityHistory.tsx"))
    assert 'role="tablist"' in content
    assert 'role="tab"' in content
    assert "aria-selected" in content


# === Global toggle switch ===

def test_notification_toggle_switch():
    """Notification global toggle should have role=switch."""
    content = _read(os.path.join(COMPONENTS, "NotificationPanel.tsx"))
    assert 'role="switch"' in content
    assert "aria-checked" in content
