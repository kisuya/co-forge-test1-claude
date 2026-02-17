"""Structure tests for discussion edit/delete UI (community-005)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
COMPONENTS = os.path.join(BASE, "components")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# --- More menu (⋯) ---

def test_discussion_more_button():
    """Own discussions should have ⋯ more button."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "⋯" in content
    assert 'data-testid="discussion-more-btn"' in content


def test_discussion_more_menu():
    """More menu should exist with edit/delete options."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="discussion-more-menu"' in content


def test_discussion_more_only_for_mine():
    """More menu should only show for own discussions (is_mine)."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "is_mine" in content


# --- Edit functionality ---

def test_discussion_edit_button():
    """Should have '수정' button in more menu."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "수정" in content
    assert 'data-testid="discussion-edit-btn"' in content


def test_discussion_edit_form():
    """Editing should show textarea form."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="discussion-edit-form"' in content
    assert 'data-testid="discussion-edit-textarea"' in content


def test_discussion_edit_save_button():
    """Edit form should have '저장' button."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "저장" in content
    assert 'data-testid="discussion-edit-save"' in content


def test_discussion_edit_cancel_button():
    """Edit form should have '취소' button."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="discussion-edit-cancel"' in content


def test_discussion_edit_maxlength():
    """Edit textarea should have max 2000 chars."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "2000" in content


def test_discussion_edit_escape_cancel():
    """Escape key should cancel editing."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "Escape" in content
    assert "handleEditCancel" in content or "editCancel" in content.lower()


# --- Delete functionality ---

def test_discussion_delete_button():
    """Should have '삭제' button in more menu."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="discussion-delete-btn"' in content


def test_discussion_delete_dialog():
    """Should show confirmation dialog before delete."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="discussion-delete-dialog"' in content
    assert 'role="dialog"' in content


def test_discussion_delete_warning():
    """Delete dialog should warn about cascading comment deletion."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "삭제하면 댓글도 함께 삭제됩니다" in content
    assert 'data-testid="discussion-delete-warning"' in content


def test_discussion_delete_confirm_button():
    """Delete dialog should have confirm and cancel buttons."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="discussion-delete-confirm"' in content
    assert 'data-testid="discussion-delete-cancel"' in content


# --- Toast feedback ---

def test_discussion_edit_success_toast():
    """Should show '수정되었습니다' toast on edit success."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "수정되었습니다" in content
    assert "addToast" in content


def test_discussion_delete_success_toast():
    """Should show '삭제되었습니다' toast on delete success."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "삭제되었습니다" in content


def test_discussion_error_toast():
    """Should show '처리에 실패했습니다' toast on error."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "처리에 실패했습니다" in content


# --- API methods ---

def test_discussions_api_update():
    """discussionsApi should have update method."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "update" in content
    assert "/api/discussions/" in content


def test_discussions_api_delete():
    """discussionsApi should have delete method."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "delete" in content
