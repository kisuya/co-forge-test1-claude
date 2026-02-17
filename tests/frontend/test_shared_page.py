"""Structure tests for shared report page and expiry (share-005)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Route exists ---


def test_shared_route_exists():
    """The /shared/[token] route should exist."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    assert os.path.exists(path), "shared/[token]/page.tsx should exist"


def test_shared_page_is_client_component():
    """Shared page should be a client component."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert '"use client"' in content


# --- Mini header ---


def test_shared_page_has_mini_header():
    """Shared page should have mini header with logo."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="shared-logo"' in content
    assert "oh-my-stock" in content


def test_shared_logo_links_to_home():
    """Logo should link to /."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert 'href="/"' in content


def test_shared_header_shows_shared_label():
    """Header should show '공유 리포트' label."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "공유 리포트" in content


# --- Report display ---


def test_shared_page_uses_report_view():
    """Shared page should use ReportView component."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "ReportView" in content


def test_shared_page_uses_share_mode():
    """ReportView should be rendered with shareMode prop."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "shareMode" in content


def test_shared_page_calls_share_api():
    """Shared page should call shareApi.getShared."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "shareApi" in content
    assert "getShared" in content


def test_shared_page_uses_params():
    """Page should use useParams to extract token."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "useParams" in content
    assert "token" in content


# --- CTA banner ---


def test_shared_page_has_cta_banner():
    """Shared page should have CTA banner."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="cta-banner"' in content


def test_cta_banner_has_signup_text():
    """CTA banner should show signup prompt."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "더 많은 분석을 보려면 가입하세요" in content


def test_cta_banner_has_signup_link():
    """CTA banner should have signup link."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="cta-signup-link"' in content
    assert "/signup" in content


# --- Expired state ---


def test_shared_page_handles_expired():
    """Shared page should show expired UI on 410."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="shared-expired"' in content
    assert "410" in content


def test_expired_shows_clock_icon():
    """Expired page should have clock icon."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "🕐" in content


def test_expired_shows_message():
    """Expired page should show expiration message."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "이 공유 링크는 만료되었습니다" in content


def test_expired_has_home_link():
    """Expired page should have 'oh-my-stock 방문하기' link."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "oh-my-stock 방문하기" in content
    assert 'data-testid="expired-home-link"' in content


# --- Not found state ---


def test_shared_page_handles_not_found():
    """Shared page should show 404 for invalid token."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="shared-not-found"' in content
    assert "404" in content


# --- OG meta ---


def test_shared_page_has_og_title():
    """Shared page should set OG title meta."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "og:title" in content
    assert "변동 분석 | oh-my-stock" in content


def test_shared_page_has_og_description():
    """Shared page should set OG description meta."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "og:description" in content


# --- Loading state ---


def test_shared_page_has_loading_skeleton():
    """Shared page should show skeleton while loading."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert 'data-testid="shared-skeleton"' in content
    assert "animate-pulse" in content


def test_report_view_supports_share_mode():
    """ReportView component should accept shareMode prop."""
    path = os.path.join(BASE, "components", "ReportView.tsx")
    content = open(path).read()
    assert "shareMode" in content
