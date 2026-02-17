"""Structure tests for nickname inline editing UI (profile-004)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Component exists ---


def test_nickname_editor_component_exists():
    """NicknameEditor component should exist."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    assert os.path.exists(path), "NicknameEditor.tsx should exist"


def test_nickname_editor_is_client_component():
    """NicknameEditor should be a client component."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    content = open(path).read()
    assert '"use client"' in content


# --- Edit mode toggle ---


def test_has_edit_button():
    """Should have ✏️ edit button."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    content = open(path).read()
    assert 'data-testid="nickname-edit-btn"' in content
    assert "✏️" in content


def test_has_nickname_display():
    """Should show nickname in display mode."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    content = open(path).read()
    assert 'data-testid="nickname-display"' in content
    assert 'data-testid="profile-nickname"' in content


def test_has_edit_mode():
    """Should have edit mode with input."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    content = open(path).read()
    assert 'data-testid="nickname-edit-mode"' in content
    assert 'data-testid="nickname-input"' in content


# --- Save and Cancel ---


def test_has_save_button():
    """Should have save button in edit mode."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    content = open(path).read()
    assert 'data-testid="nickname-save-btn"' in content
    assert "저장" in content


def test_has_cancel_button():
    """Should have cancel button in edit mode."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    content = open(path).read()
    assert 'data-testid="nickname-cancel-btn"' in content
    assert "취소" in content


# --- API integration ---


def test_calls_profile_update_api():
    """Should call profileApi.updateNickname on save."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    content = open(path).read()
    assert "profileApi" in content
    assert "updateNickname" in content


def test_profile_api_has_update_nickname():
    """profileApi should have updateNickname method."""
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "updateNickname" in content


# --- Keyboard shortcuts ---


def test_enter_key_saves():
    """Enter key should trigger save."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    content = open(path).read()
    assert "Enter" in content


def test_escape_key_cancels():
    """Escape key should trigger cancel."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    content = open(path).read()
    assert "Escape" in content


# --- Input constraints ---


def test_input_has_max_length():
    """Input should have maxLength=20."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    content = open(path).read()
    assert "maxLength" in content
    assert "20" in content


# --- Error handling ---


def test_handles_409_duplicate():
    """Should show toast on 409 duplicate nickname."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    content = open(path).read()
    assert "409" in content
    assert "이미 사용 중인 닉네임입니다" in content


def test_handles_422_validation():
    """Should show field error on 422 validation error."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    content = open(path).read()
    assert "422" in content
    assert 'data-testid="nickname-field-error"' in content
    assert "2~20자" in content


# --- Success toast ---


def test_shows_success_toast():
    """Should show success toast on nickname change."""
    path = os.path.join(BASE, "components", "NicknameEditor.tsx")
    content = open(path).read()
    assert "닉네임이 변경되었습니다" in content
    assert "addToast" in content


# --- Mypage integration ---


def test_mypage_uses_nickname_editor():
    """Mypage should import and use NicknameEditor."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert "NicknameEditor" in content
