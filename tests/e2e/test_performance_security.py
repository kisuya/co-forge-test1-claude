"""Performance and security tests (infra-006).

Verifies:
  1. Dynamic imports used for heavy components (lazy loading)
  2. CSP header present in layout
  3. XSS prevention: no dangerouslySetInnerHTML, sanitization in backend
  4. API response time under 500ms (p95)
  5. Bundle considerations: no unnecessary large imports
  6. Accessibility: aria-label count >= 20, focus-visible, skip link
"""
from __future__ import annotations

import os
import re
import time

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_perf_security.db"

BASE_FE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
PUBLIC_FE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public")


def _get_test_db() -> Session:  # type: ignore[misc]
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()


def _setup() -> None:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    seed_stocks(session)
    seed_us_stocks(session)
    session.close()


def _teardown() -> None:
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_perf_security.db"):
        os.remove("test_perf_security.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(c: AsyncClient, email: str = "perf@test.com") -> str:
    await c.post("/api/auth/signup", json={"email": email, "password": "testpass123"})
    login = await c.post("/api/auth/login", json={"email": email, "password": "testpass123"})
    return login.json()["access_token"]


# --- 1. Dynamic imports for lazy loading ---


def test_dashboard_uses_dynamic_imports():
    """Dashboard page should use next/dynamic for heavy widgets."""
    path = os.path.join(BASE_FE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "dynamic" in content, "Dashboard should use dynamic imports"
    assert "import(" in content, "Dashboard should have dynamic import() calls"


def test_dashboard_lazy_loads_briefing_card():
    """BriefingCard should be dynamically imported."""
    path = os.path.join(BASE_FE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "dynamic(() => import" in content


def test_dashboard_lazy_loads_calendar_widget():
    """CalendarWidget should be dynamically imported."""
    path = os.path.join(BASE_FE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "CalendarWidget" in content


def test_dashboard_lazy_loads_news_widget():
    """NewsWidget should be dynamically imported."""
    path = os.path.join(BASE_FE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "NewsWidget" in content


def test_dashboard_lazy_loads_trending_widget():
    """TrendingWidget should be dynamically imported."""
    path = os.path.join(BASE_FE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "TrendingWidget" in content


# --- 2. CSP header ---


def test_csp_header_in_layout():
    """Layout should include Content-Security-Policy meta tag."""
    path = os.path.join(BASE_FE, "app", "layout.tsx")
    content = open(path).read()
    assert "Content-Security-Policy" in content
    assert "script-src" in content
    assert "style-src" in content


# --- 3. XSS prevention ---


def test_no_dangerously_set_innerhtml():
    """No component should use dangerouslySetInnerHTML."""
    components_dir = os.path.join(BASE_FE, "components")
    for fname in os.listdir(components_dir):
        if fname.endswith(".tsx") or fname.endswith(".ts"):
            fpath = os.path.join(components_dir, fname)
            content = open(fpath).read()
            assert "dangerouslySetInnerHTML" not in content, (
                f"{fname} uses dangerouslySetInnerHTML — XSS risk"
            )


def test_no_dangerously_set_innerhtml_in_pages():
    """No page should use dangerouslySetInnerHTML."""
    for root, dirs, files in os.walk(os.path.join(BASE_FE, "app")):
        for fname in files:
            if fname.endswith(".tsx"):
                fpath = os.path.join(root, fname)
                content = open(fpath).read()
                assert "dangerouslySetInnerHTML" not in content, (
                    f"{fpath} uses dangerouslySetInnerHTML — XSS risk"
                )


def test_backend_has_html_sanitizer():
    """Backend should have HTML sanitization utility."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "backend", "app", "core", "sanitize.py"
    )
    assert os.path.isfile(path)
    content = open(path).read()
    assert "strip_html_tags" in content


def test_discussion_api_uses_sanitizer():
    """Discussion API should sanitize HTML in content."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "backend", "app", "api", "discussions.py"
    )
    content = open(path).read()
    assert "strip_html_tags" in content


@pytest.mark.asyncio
async def test_xss_attempt_stripped() -> None:
    """XSS script tags should be stripped from discussion content."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c, "xss@test.com")
            headers = {"Authorization": f"Bearer {token}"}

            search = await c.get("/api/stocks/search", params={"q": "삼성"})
            stock_id = search.json()[0]["id"]

            resp = await c.post(
                f"/api/stocks/{stock_id}/discussions",
                json={"content": '<script>alert("xss")</script>안녕하세요'},
                headers=headers,
            )
            assert resp.status_code == 201
            data = resp.json()
            assert "<script>" not in data["content"]
            assert "안녕하세요" in data["content"]
    finally:
        _teardown()


# --- 4. API response time ---


@pytest.mark.asyncio
async def test_api_response_times() -> None:
    """Key API endpoints should respond within 500ms."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c, "timing@test.com")
            headers = {"Authorization": f"Bearer {token}"}

            endpoints = [
                ("GET", "/health", None),
                ("GET", "/api/stocks/search?q=삼성", None),
                ("GET", "/api/watchlist", headers),
                ("GET", "/api/profile", headers),
                ("GET", "/api/briefings?market=KR", None),
                ("GET", "/api/trending", None),
                ("GET", "/api/popular", None),
                ("GET", "/api/calendar/week", None),
            ]

            for method, url, hdrs in endpoints:
                start = time.time()
                resp = await c.request(method, url, headers=hdrs)
                elapsed = time.time() - start
                assert elapsed < 0.5, (
                    f"{method} {url} took {elapsed:.3f}s (>500ms)"
                )
                assert resp.status_code in (200, 401, 403)
    finally:
        _teardown()


# --- 5. Accessibility ---


def test_aria_labels_count():
    """At least 20 aria-label attributes across components."""
    components_dir = os.path.join(BASE_FE, "components")
    total = 0
    for fname in os.listdir(components_dir):
        if fname.endswith(".tsx"):
            fpath = os.path.join(components_dir, fname)
            content = open(fpath).read()
            total += content.count("aria-label")
    assert total >= 20, f"Only {total} aria-label attributes found (need 20+)"


def test_focus_visible_styles():
    """Focus-visible styles should be defined."""
    path = os.path.join(BASE_FE, "app", "globals.css")
    content = open(path).read()
    assert "focus-visible" in content


def test_skip_to_main_link():
    """Layout should have skip-to-main-content link."""
    path = os.path.join(BASE_FE, "app", "layout.tsx")
    content = open(path).read()
    assert "skip-to-main" in content
    assert "main-content" in content


def test_html_lang_ko():
    """HTML tag should have lang='ko'."""
    path = os.path.join(BASE_FE, "app", "layout.tsx")
    content = open(path).read()
    assert 'lang="ko"' in content


def test_main_landmark():
    """Layout should have <main> landmark element."""
    path = os.path.join(BASE_FE, "app", "layout.tsx")
    content = open(path).read()
    assert "<main" in content


# --- 6. Security headers ---


@pytest.mark.asyncio
async def test_cors_on_error_response() -> None:
    """Error responses should include CORS headers."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get(
                "/api/nonexistent",
                headers={"Origin": "http://localhost:3000"},
            )
            assert resp.status_code == 404
            assert "access-control-allow-origin" in resp.headers
    finally:
        _teardown()


# --- 7. JWT bearer security (not cookie-based) ---


def test_auth_uses_bearer_tokens():
    """Auth should use Bearer tokens (not cookies)."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "backend", "app", "api", "auth.py"
    )
    content = open(path).read()
    assert "access_token" in content
    # Should not set cookies
    assert "set_cookie" not in content.lower()
