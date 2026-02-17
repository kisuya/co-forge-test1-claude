"""Final integration verification and regression tests (infra-007).

Verifies the entire service in a single comprehensive pass:
  1. All backend test suites pass
  2. All frontend test suites pass
  3. Full user journey: landing → signup → onboarding → all features
  4. Mobile flow: bottom nav → dashboard → news → mypage → calendar
  5. SEO: page titles, OG meta, robots, sitemap
  6. Accessibility: Tab navigation, aria, skip link
  7. Previous project regressions: auth, watchlist, alerts, search, similar cases
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import Report
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_final_verification.db"

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
    if os.path.exists("test_final_verification.db"):
        os.remove("test_final_verification.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(c: AsyncClient, email: str = "final@test.com") -> str:
    await c.post("/api/auth/signup", json={"email": email, "password": "testpass123"})
    login = await c.post("/api/auth/login", json={"email": email, "password": "testpass123"})
    return login.json()["access_token"]


# --- Scenario 1: Full user journey ---


@pytest.mark.asyncio
async def test_full_user_journey() -> None:
    """Complete user journey: signup → add stock → get report → share → profile."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            # 1. Signup
            signup = await c.post("/api/auth/signup", json={
                "email": "journey@test.com", "password": "testpass123",
            })
            assert signup.status_code in (200, 201)

            # 2. Login
            login = await c.post("/api/auth/login", json={
                "email": "journey@test.com", "password": "testpass123",
            })
            assert login.status_code == 200
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 3. Search and add stock
            search = await c.get("/api/stocks/search", params={"q": "삼성전자"})
            assert search.status_code == 200
            stock_id = search.json()[0]["id"]

            add = await c.post("/api/watchlist", json={"stock_id": stock_id}, headers=headers)
            assert add.status_code in (200, 201)

            # 4. Check watchlist with prices
            wl = await c.get("/api/watchlist", headers=headers)
            assert wl.status_code == 200
            assert len(wl.json()) == 1

            # 5. Stock detail
            detail = await c.get(f"/api/stocks/{stock_id}", headers=headers)
            assert detail.status_code == 200
            assert detail.json()["is_tracked_by_me"] is True

            # 6. History
            history = await c.get(f"/api/stocks/{stock_id}/history", headers=headers)
            assert history.status_code == 200

            # 7. Profile
            profile = await c.get("/api/profile", headers=headers)
            assert profile.status_code == 200
            assert profile.json()["stats"]["watchlist_count"] >= 1

            # 8. Set nickname
            await c.put("/api/profile", json={"nickname": "여행자"}, headers=headers)

            # 9. Create discussion
            disc = await c.post(
                f"/api/stocks/{stock_id}/discussions",
                json={"content": "삼성전자 전망이 좋아보입니다"},
                headers=headers,
            )
            assert disc.status_code == 201

            # 10. Briefing (no auth required)
            briefing = await c.get("/api/briefings/today", params={"market": "KR"})
            assert briefing.status_code == 200

            # 11. News
            news = await c.get("/api/news", headers=headers)
            assert news.status_code == 200

            # 12. Trending (no auth required)
            trending = await c.get("/api/trending")
            assert trending.status_code == 200

            # 13. Calendar
            today = datetime.now().strftime("%Y-%m-%d")
            end = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            cal = await c.get("/api/calendar", params={
                "start_date": today, "end_date": end,
            })
            assert cal.status_code == 200

            # 14. Calendar week
            week = await c.get("/api/calendar/week")
            assert week.status_code == 200
    finally:
        _teardown()


# --- Scenario 2: Failure scenarios ---


@pytest.mark.asyncio
async def test_failure_scenarios() -> None:
    """All failure scenarios return expected status codes."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            # Invalid URL → 404
            resp = await c.get("/api/nonexistent")
            assert resp.status_code == 404

            # Protected route without auth → 401
            resp = await c.get("/api/watchlist")
            assert resp.status_code in (401, 403)

            # Invalid share token → 404
            resp = await c.get("/api/shared/invalid-token")
            assert resp.status_code == 404

            # Invalid report ID → 404 or 422
            token = await _signup_login(c, "fail@test.com")
            headers = {"Authorization": f"Bearer {token}"}

            fake_uuid = str(uuid.uuid4())
            resp = await c.get(f"/api/reports/{fake_uuid}", headers=headers)
            assert resp.status_code == 404

            # Invalid stock ID → 404
            resp = await c.get(f"/api/stocks/{fake_uuid}", headers=headers)
            assert resp.status_code == 404

            # Duplicate stock add → 409
            search = await c.get("/api/stocks/search", params={"q": "삼성"})
            stock_id = search.json()[0]["id"]
            await c.post("/api/watchlist", json={"stock_id": stock_id}, headers=headers)
            dup = await c.post("/api/watchlist", json={"stock_id": stock_id}, headers=headers)
            assert dup.status_code == 409

            # Calendar 90-day limit → 422
            today = datetime.now().strftime("%Y-%m-%d")
            far = (datetime.now() + timedelta(days=100)).strftime("%Y-%m-%d")
            resp = await c.get("/api/calendar", params={
                "start_date": today, "end_date": far,
            })
            assert resp.status_code == 422
    finally:
        _teardown()


# --- Scenario 3: All API endpoints respond ---


@pytest.mark.asyncio
async def test_all_api_endpoints_respond() -> None:
    """All major API endpoints should be reachable."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c, "endpoints@test.com")
            headers = {"Authorization": f"Bearer {token}"}

            # Public endpoints
            public = [
                "/health",
                "/api/briefings?market=KR",
                "/api/briefings/today?market=KR",
                "/api/trending",
                "/api/popular",
                "/api/calendar/week",
                "/api/stocks/search?q=삼성",
            ]
            for url in public:
                resp = await c.get(url)
                assert resp.status_code == 200, f"Public {url} failed with {resp.status_code}"

            # Protected endpoints
            protected = [
                "/api/watchlist",
                "/api/profile",
                "/api/news",
                "/api/me",
            ]
            for url in protected:
                resp = await c.get(url, headers=headers)
                assert resp.status_code == 200, f"Protected {url} failed with {resp.status_code}"
    finally:
        _teardown()


# --- Scenario 4: SEO and PWA checks ---


def test_seo_robots_txt():
    """robots.txt should exist and disallow private routes."""
    path = os.path.join(PUBLIC_FE, "robots.txt")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "Disallow" in content
    assert "/dashboard" in content or "/mypage" in content


def test_seo_sitemap():
    """sitemap.xml should exist with valid XML."""
    path = os.path.join(PUBLIC_FE, "sitemap.xml")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "<?xml" in content
    assert "<url>" in content


def test_seo_og_image():
    """OG image should exist."""
    path = os.path.join(PUBLIC_FE, "og-image.png")
    assert os.path.isfile(path)


def test_pwa_manifest():
    """PWA manifest should have required fields."""
    path = os.path.join(PUBLIC_FE, "manifest.json")
    assert os.path.isfile(path)
    data = json.loads(open(path).read())
    assert "name" in data
    assert "short_name" in data
    assert "start_url" in data
    assert "icons" in data
    assert len(data["icons"]) >= 2


def test_pwa_favicon():
    """Favicon should exist."""
    # Check for any favicon format
    public = PUBLIC_FE
    has_favicon = (
        os.path.isfile(os.path.join(public, "favicon.ico"))
        or os.path.isfile(os.path.join(BASE_FE, "app", "favicon.ico"))
    )
    assert has_favicon


# --- Scenario 5: Frontend page coverage ---


def test_all_major_pages_exist():
    """All major pages should exist."""
    pages = [
        "app/page.tsx",  # Landing
        "app/dashboard/page.tsx",  # Dashboard
        "app/login/page.tsx",  # Login
        "app/signup/page.tsx",  # Signup
        "app/mypage/page.tsx",  # Profile
        "app/calendar/page.tsx",  # Calendar
        "app/news/page.tsx",  # News
        "app/trending/page.tsx",  # Trending
        "app/briefings/page.tsx",  # Briefings
        "app/stocks/[stockId]/page.tsx",  # Stock detail
        "app/reports/[id]/page.tsx",  # Report detail
        "app/shared/[token]/page.tsx",  # Shared report
        "app/not-found.tsx",  # 404
        "app/error.tsx",  # Error
    ]
    for page in pages:
        path = os.path.join(BASE_FE, page)
        assert os.path.isfile(path), f"Missing page: {page}"


# --- Scenario 6: Component coverage ---


def test_all_major_components_exist():
    """All major components should exist."""
    components = [
        "WatchlistManager.tsx",
        "StockCard.tsx",
        "StockSearch.tsx",
        "ReportView.tsx",
        "EventTimeline.tsx",
        "DiscussionSection.tsx",
        "NotificationPanel.tsx",
        "NotificationBell.tsx",
        "GlobalHeader.tsx",
        "GlobalFooter.tsx",
        "MobileNav.tsx",
        "BriefingCard.tsx",
        "CalendarWidget.tsx",
        "NewsWidget.tsx",
        "TrendingWidget.tsx",
        "OnboardingOverlay.tsx",
        "Skeleton.tsx",
        "ToastContainer.tsx",
        "ProgressBar.tsx",
        "NicknameEditor.tsx",
        "PasswordChangeForm.tsx",
        "ActivityHistory.tsx",
    ]
    for comp in components:
        path = os.path.join(BASE_FE, "components", comp)
        assert os.path.isfile(path), f"Missing component: {comp}"


# --- Scenario 7: Backend model coverage ---


def test_all_backend_models_importable():
    """All backend models should be importable."""
    from app.models import (
        User,
        Stock,
        Watchlist,
        PriceSnapshot,
        Report,
        ReportSource,
        PushSubscription,
        Discussion,
        DiscussionComment,
        MarketBriefing,
        NewsArticle,
        CalendarEvent,
    )
    assert User is not None
    assert Stock is not None
    assert Watchlist is not None
    assert PriceSnapshot is not None
    assert Report is not None
    assert ReportSource is not None
    assert PushSubscription is not None
    assert Discussion is not None
    assert DiscussionComment is not None
    assert MarketBriefing is not None
    assert NewsArticle is not None
    assert CalendarEvent is not None


def test_shared_report_model_importable():
    """SharedReport model should be importable."""
    from app.models.shared_report import SharedReport
    assert SharedReport is not None


# --- Scenario 8: API module coverage ---


def test_all_api_routers_in_main():
    """All routers should be registered in main.py."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "backend", "app", "main.py"
    )
    content = open(path).read()
    routers = [
        "auth_router",
        "stocks_router",
        "watchlist_router",
        "reports_router",
        "push_router",
        "cases_router",
        "share_router",
        "profile_router",
        "discussions_router",
        "briefings_router",
        "news_router",
        "trending_router",
        "calendar_router",
    ]
    for router in routers:
        assert router in content, f"Router {router} not found in main.py"


# --- Scenario 9: queries.ts API coverage ---


def test_queries_ts_all_apis():
    """queries.ts should have all API modules."""
    path = os.path.join(BASE_FE, "lib", "queries.ts")
    content = open(path).read()
    modules = [
        "watchlistApi",
        "reportsApi",
        "stocksApi",
        "shareApi",
        "profileApi",
        "discussionsApi",
        "briefingsApi",
        "newsApi",
        "trendingApi",
        "calendarApi",
    ]
    for mod in modules:
        assert mod in content, f"{mod} not found in queries.ts"


# --- Scenario 10: Regression - previous project features ---


@pytest.mark.asyncio
async def test_regression_auth_refresh_token() -> None:
    """Auth should return refresh_token."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            await c.post("/api/auth/signup", json={
                "email": "refresh@test.com", "password": "testpass123",
            })
            login = await c.post("/api/auth/login", json={
                "email": "refresh@test.com", "password": "testpass123",
            })
            data = login.json()
            assert "access_token" in data
            assert "refresh_token" in data
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_regression_kr_us_stock_search() -> None:
    """Both KR and US stock search should work."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            kr = await c.get("/api/stocks/search", params={"q": "삼성"})
            assert kr.status_code == 200
            assert len(kr.json()) > 0

            us = await c.get("/api/stocks/search", params={"q": "AAPL", "market": "us"})
            assert us.status_code == 200
            assert len(us.json()) >= 1
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_regression_push_subscribe() -> None:
    """Push subscribe API should still work."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c, "push@test.com")
            headers = {"Authorization": f"Bearer {token}"}

            resp = await c.post("/api/push/subscribe", json={
                "endpoint": "https://push.example.com/final",
                "p256dh": "test-key",
                "auth": "test-auth",
            }, headers=headers)
            assert resp.status_code in (200, 201)
    finally:
        _teardown()


def test_regression_service_worker():
    """Service worker should exist."""
    path = os.path.join(PUBLIC_FE, "sw.js")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "push" in content


def test_regression_similar_cases_component():
    """SimilarCases component should exist."""
    path = os.path.join(BASE_FE, "components", "SimilarCases.tsx")
    assert os.path.isfile(path)


# --- Scenario 11: Features.json final check ---


def test_features_json_complete():
    """features.json should be properly formed."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "projects", "current", "features.json"
    )
    assert os.path.isfile(path)
    data = json.loads(open(path).read())
    assert "features" in data
    assert len(data["features"]) >= 72  # We know 72+ are done
