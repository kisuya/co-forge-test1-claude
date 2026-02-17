"""Structure tests for discussion detail and comments UI (community-006)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
COMPONENTS = os.path.join(BASE, "components")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# --- Inline expansion (accordion) ---

def test_discussion_toggle_exists():
    """Discussion items should be clickable for inline expansion."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="discussion-toggle"' in content
    assert "expandedId" in content


def test_discussion_full_content():
    """Expanded discussion should show full content."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="discussion-full-content"' in content


def test_discussion_collapse():
    """Clicking again should collapse (accordion toggle)."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    # Toggle logic: clicking same ID collapses
    assert "expandedId === discussionId" in content or "expandedId === d.id" in content


def test_discussion_comments_section():
    """Expanded discussion should show comments section."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="discussion-comments-section"' in content


# --- Comment list ---

def test_comment_list_exists():
    """Should have comment-list testid."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="comment-list"' in content


def test_comment_item_exists():
    """Each comment should have comment-item testid."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="comment-item"' in content


def test_comment_author():
    """Comment should show author name in bold 12px."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="comment-author"' in content
    assert "font-bold" in content
    assert '"12px"' in content


def test_comment_content():
    """Comment content should be 14px."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="comment-content"' in content
    assert '"14px"' in content


def test_comment_time():
    """Comment should show time in 12px gray."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="comment-time"' in content
    assert "text-gray-400" in content


# --- Comment creation ---

def test_comment_form():
    """Should have comment form with input."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="comment-form"' in content


def test_comment_input():
    """Should have comment input with placeholder."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "댓글을 입력하세요" in content
    assert 'data-testid="comment-input"' in content


def test_comment_input_maxlength():
    """Comment input should have max 500 chars."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "500" in content
    assert "maxLength" in content


def test_comment_submit_button():
    """Should have '등록' submit button."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "등록" in content
    assert 'data-testid="comment-submit-btn"' in content


# --- Non-logged-in comment state ---

def test_comment_login_notice():
    """Non-logged-in should show '로그인이 필요합니다'."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "로그인이 필요합니다" in content
    assert 'data-testid="comment-login-notice"' in content


def test_comment_input_disabled_when_not_logged_in():
    """Comment input should be disabled when not logged in."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "disabled" in content
    assert "loggedIn" in content


# --- Empty comments ---

def test_empty_comments():
    """Should show '아직 댓글이 없습니다' when no comments."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "아직 댓글이 없습니다" in content
    assert 'data-testid="empty-comments"' in content


# --- Comment loading error ---

def test_comments_error():
    """Should show error message when comments fail to load."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "댓글을 불러올 수 없습니다" in content
    assert 'data-testid="comments-error"' in content


# --- Comment deletion ---

def test_comment_delete_button():
    """Own comments should have delete button."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="comment-delete-btn"' in content


def test_comment_delete_only_mine():
    """Delete button should only show for own comments."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "is_mine" in content
    assert "comment-delete-btn" in content


# --- Mobile touch target ---

def test_mobile_touch_target():
    """Discussion toggle area should have min-height 48px for touch."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "min-h-[48px]" in content


# --- API methods ---

def test_comments_api_list():
    """discussionsApi should have listComments method."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "listComments" in content
    assert "/comments" in content


def test_comments_api_create():
    """discussionsApi should have createComment method."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "createComment" in content


def test_comments_api_delete():
    """discussionsApi should have deleteComment method."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "deleteComment" in content


# --- Types ---

def test_comment_type_exists():
    """types/index.ts should have CommentItem type."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "CommentItem" in content


def test_comment_type_fields():
    """CommentItem should have required fields."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "author_name" in content
    assert "is_mine" in content
