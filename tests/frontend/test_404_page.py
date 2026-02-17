"""Structure tests for custom 404 page (ui-027)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def test_not_found_exists():
    """not-found.tsx should exist in app directory."""
    path = os.path.join(BASE, "app", "not-found.tsx")
    assert os.path.exists(path), "app/not-found.tsx should exist"


def test_not_found_is_client_component():
    """not-found should be a client component."""
    path = os.path.join(BASE, "app", "not-found.tsx")
    content = open(path).read()
    assert '"use client"' in content


def test_not_found_has_testid():
    """Should have not-found-page testid."""
    path = os.path.join(BASE, "app", "not-found.tsx")
    content = open(path).read()
    assert 'data-testid="not-found-page"' in content


def test_not_found_shows_404():
    """Should show 404 code with 72px bold."""
    path = os.path.join(BASE, "app", "not-found.tsx")
    content = open(path).read()
    assert "404" in content
    assert "72px" in content
    assert "font-bold" in content
    assert "gray-300" in content


def test_not_found_title():
    """Should show title '페이지를 찾을 수 없습니다' at 24px."""
    path = os.path.join(BASE, "app", "not-found.tsx")
    content = open(path).read()
    assert "페이지를 찾을 수 없습니다" in content
    assert "24px" in content


def test_not_found_description():
    """Should show description at 14px gray."""
    path = os.path.join(BASE, "app", "not-found.tsx")
    content = open(path).read()
    assert "요청하신 페이지가 존재하지 않거나 이동되었습니다" in content
    assert "14px" in content
    assert "gray-500" in content


def test_not_found_dashboard_link():
    """Logged in users should see dashboard link."""
    path = os.path.join(BASE, "app", "not-found.tsx")
    content = open(path).read()
    assert "대시보드로 돌아가기" in content
    assert "/dashboard" in content


def test_not_found_home_link():
    """Non-logged in users should see home link."""
    path = os.path.join(BASE, "app", "not-found.tsx")
    content = open(path).read()
    assert "홈으로 돌아가기" in content


def test_not_found_login_check():
    """Should check login status for conditional rendering."""
    path = os.path.join(BASE, "app", "not-found.tsx")
    content = open(path).read()
    assert "isLoggedIn" in content


def test_not_found_centered():
    """Should be centered layout."""
    path = os.path.join(BASE, "app", "not-found.tsx")
    content = open(path).read()
    assert "items-center" in content
    assert "justify-center" in content
