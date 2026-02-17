"""Structure tests for discussion list and creation UI (community-004)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
COMPONENTS = os.path.join(BASE, "components")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# --- Component existence ---

def test_discussion_section_component_exists():
    """DiscussionSection component should exist."""
    path = os.path.join(COMPONENTS, "DiscussionSection.tsx")
    assert os.path.isfile(path)


def test_discussion_section_is_client_component():
    """DiscussionSection must be a client component."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert '"use client"' in content


# --- Integration with stock detail page ---

def test_stock_detail_imports_discussion():
    """Stock detail page should import DiscussionSection."""
    content = _read(os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx"))
    assert "DiscussionSection" in content
    assert "discussion" in content.lower()


def test_stock_detail_renders_discussion():
    """Stock detail page should render DiscussionSection with stockId."""
    content = _read(os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx"))
    assert "<DiscussionSection" in content
    assert "stockId" in content


# --- Discussion section structure ---

def test_discussion_section_testid():
    """Should have discussion-section testid."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="discussion-section"' in content


def test_discussion_title():
    """Should show '💬 토론' title."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "토론" in content
    assert 'data-testid="discussion-title"' in content


# --- Write form ---

def test_discussion_textarea():
    """Should have textarea with placeholder."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "이 종목에 대한 의견을 남겨보세요" in content
    assert 'data-testid="discussion-textarea"' in content


def test_discussion_textarea_maxlength():
    """Textarea should have max 2000 chars."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "2000" in content
    assert "maxLength" in content


def test_discussion_submit_button():
    """Should have '게시' submit button."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "게시" in content
    assert 'data-testid="discussion-submit-btn"' in content


def test_discussion_form_testid():
    """Should have discussion-form testid."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="discussion-form"' in content


# --- Non-logged-in state ---

def test_discussion_login_overlay():
    """Non-logged-in: should show login overlay."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "로그인 후 작성할 수 있습니다" in content
    assert 'data-testid="discussion-login-overlay"' in content


def test_discussion_login_link():
    """Non-logged-in: should have login link."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "/login" in content
    assert 'data-testid="discussion-login-link"' in content


def test_discussion_textarea_disabled_when_not_logged_in():
    """Textarea should be disabled when not logged in."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "disabled" in content
    assert "loggedIn" in content or "isLoggedIn" in content


# --- Discussion list ---

def test_discussion_list_testid():
    """Should have discussion-list testid."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="discussion-list"' in content


def test_discussion_item_testid():
    """Each item should have discussion-item testid."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert 'data-testid="discussion-item"' in content


def test_discussion_item_author():
    """Item should show author name (bold)."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "author_name" in content
    assert 'data-testid="discussion-author"' in content
    assert "font-bold" in content


def test_discussion_item_time():
    """Item should show relative time."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "분 전" in content
    assert "시간 전" in content
    assert "일 전" in content
    assert 'data-testid="discussion-time"' in content


def test_discussion_item_content_ellipsis():
    """Item content should be max 2 lines with ellipsis."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "line-clamp-2" in content
    assert 'data-testid="discussion-content"' in content


def test_discussion_item_comment_count():
    """Item should show comment count with 💬."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "comment_count" in content
    assert 'data-testid="discussion-comment-count"' in content


# --- Empty state ---

def test_discussion_empty_state():
    """Should show empty state message."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "아직 토론이 없습니다. 첫 번째 글을 작성해보세요!" in content
    assert 'data-testid="empty-discussions"' in content


# --- Pagination ---

def test_discussion_load_more_button():
    """Should have '이전 글 더 보기' button for pagination."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "이전 글 더 보기" in content
    assert 'data-testid="discussion-load-more"' in content


def test_discussion_pagination_uses_page():
    """Should use page-based pagination."""
    content = _read(os.path.join(COMPONENTS, "DiscussionSection.tsx"))
    assert "page" in content
    assert "hasMore" in content


# --- API integration ---

def test_discussions_api_exists():
    """queries.ts should have discussionsApi."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "discussionsApi" in content


def test_discussions_api_list():
    """discussionsApi should have list method."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "discussions" in content.lower()
    assert "/api/stocks/" in content


def test_discussions_api_create():
    """discussionsApi should have create method."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "create" in content
    assert "content" in content


# --- Types ---

def test_discussion_types_exist():
    """types/index.ts should have DiscussionItem type."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "DiscussionItem" in content
    assert "DiscussionListResponse" in content


def test_discussion_type_fields():
    """DiscussionItem should have required fields."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "author_name" in content
    assert "comment_count" in content
    assert "is_mine" in content
