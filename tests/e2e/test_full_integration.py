"""Full feature E2E integration tests (infra-005).

Verifies:
  1. Landing page → signup → onboarding flow
  2. Report share → public access → expiry handling
  3. Profile → nickname → password change
  4. Discussions → create → comment → edit → delete
  5. Briefing API → card data
  6. News feed → filtering
  7. Trending → popular API
  8. Calendar → week events
  9. Mobile navigation structure
  10. SEO: page titles, OG meta
  11. Failure scenarios: 404, auth redirect, expired share
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.market_briefing import MarketBriefing
from app.models.news_article import NewsArticle
from app.models.report import Report
from app.models.shared_report import SharedReport
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_full_integration.db"

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
    if os.path.exists("test_full_integration.db"):
        os.remove("test_full_integration.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(c: AsyncClient, email: str = "full@test.com") -> str:
    await c.post("/api/auth/signup", json={"email": email, "password": "testpass123"})
    login = await c.post("/api/auth/login", json={"email": email, "password": "testpass123"})
    return login.json()["access_token"]


# --- Scenario 1: Signup + onboarding ---


@pytest.mark.asyncio
async def test_signup_and_dashboard_access() -> None:
    """Signup → login → access dashboard endpoints."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            signup = await c.post("/api/auth/signup", json={
                "email": "newuser@test.com", "password": "testpass123",
            })
            assert signup.status_code in (200, 201)

            login = await c.post("/api/auth/login", json={
                "email": "newuser@test.com", "password": "testpass123",
            })
            assert login.status_code == 200
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Access watchlist (should be empty)
            wl = await c.get("/api/watchlist", headers=headers)
            assert wl.status_code == 200
            assert len(wl.json()) == 0

            # Access profile
            profile = await c.get("/api/profile", headers=headers)
            assert profile.status_code == 200
            assert profile.json()["email"] == "newuser@test.com"
    finally:
        _teardown()


# --- Scenario 2: Add stock → get report → share → public access ---


@pytest.mark.asyncio
async def test_report_share_and_public_access() -> None:
    """Share a report and access it publicly."""
    _setup()
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        import bcrypt
        user = User(
            email="sharer@test.com",
            password_hash=bcrypt.hashpw(b"testpass123", bcrypt.gensalt()).decode(),
        )
        session.add(user)
        session.flush()

        stock = session.query(Stock).filter(Stock.code == "005930").first()

        wl = Watchlist(user_id=user.id, stock_id=stock.id, threshold=3.0)
        session.add(wl)

        report = Report(
            stock_id=stock.id,
            trigger_price=Decimal("65000"),
            trigger_change_pct=5.5,
            status="completed",
            summary="삼성전자 급등 분석",
            analysis={"causes": [{"reason": "실적 호조", "confidence": "high"}]},
        )
        session.add(report)
        session.commit()
        report_id = str(report.id)
        session.close()

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            login = await c.post("/api/auth/login", json={
                "email": "sharer@test.com", "password": "testpass123",
            })
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Share report
            share = await c.post(f"/api/reports/{report_id}/share", headers=headers)
            assert share.status_code == 200
            share_data = share.json()
            assert "share_token" in share_data
            share_token = share_data["share_token"]

            # Public access (no auth)
            public = await c.get(f"/api/shared/{share_token}")
            assert public.status_code == 200
            pub_data = public.json()
            assert pub_data["stock_name"] == "삼성전자"
            assert "report" in pub_data

            # Duplicate share returns same token
            share2 = await c.post(f"/api/reports/{report_id}/share", headers=headers)
            assert share2.json()["share_token"] == share_token
    finally:
        _teardown()


# --- Scenario 3: Expired share link → 410 ---


@pytest.mark.asyncio
async def test_expired_share_returns_410() -> None:
    """Expired share token returns 410 Gone."""
    _setup()
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        import bcrypt
        user = User(
            email="expired@test.com",
            password_hash=bcrypt.hashpw(b"testpass123", bcrypt.gensalt()).decode(),
        )
        session.add(user)
        session.flush()

        stock = session.query(Stock).first()
        report = Report(
            stock_id=stock.id, trigger_price=Decimal("50000"),
            trigger_change_pct=3.0, status="completed",
        )
        session.add(report)
        session.flush()

        shared = SharedReport(
            report_id=report.id,
            created_by=user.id,
        )
        shared.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        session.add(shared)
        session.commit()
        token = shared.share_token
        session.close()

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get(f"/api/shared/{token}")
            assert resp.status_code == 410
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_invalid_share_token_returns_404() -> None:
    """Invalid share token returns 404."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/shared/nonexistent-token")
            assert resp.status_code == 404
    finally:
        _teardown()


# --- Scenario 4: Profile → nickname → password ---


@pytest.mark.asyncio
async def test_profile_nickname_and_password() -> None:
    """User can set nickname and change password."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c, "profile@test.com")
            headers = {"Authorization": f"Bearer {token}"}

            # Get profile
            profile = await c.get("/api/profile", headers=headers)
            assert profile.status_code == 200

            # Set nickname
            nick = await c.put("/api/profile", json={"nickname": "테스터"}, headers=headers)
            assert nick.status_code == 200

            # Verify nickname
            profile2 = await c.get("/api/profile", headers=headers)
            assert profile2.json()["nickname"] == "테스터"

            # Duplicate nickname (create another user)
            token2 = await _signup_login(c, "profile2@test.com")
            headers2 = {"Authorization": f"Bearer {token2}"}
            dup = await c.put("/api/profile", json={"nickname": "테스터"}, headers=headers2)
            assert dup.status_code == 409

            # Change password
            pw = await c.put("/api/profile/password", json={
                "current_password": "testpass123",
                "new_password": "newpass456",
            }, headers=headers)
            assert pw.status_code == 200

            # Login with new password
            login = await c.post("/api/auth/login", json={
                "email": "profile@test.com", "password": "newpass456",
            })
            assert login.status_code == 200

            # Old password fails
            login_old = await c.post("/api/auth/login", json={
                "email": "profile@test.com", "password": "testpass123",
            })
            assert login_old.status_code in (400, 401)
    finally:
        _teardown()


# --- Scenario 5: Discussion CRUD + comments ---


@pytest.mark.asyncio
async def test_discussion_full_flow() -> None:
    """Create discussion, comment, edit, delete."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c, "discuss@test.com")
            headers = {"Authorization": f"Bearer {token}"}

            search = await c.get("/api/stocks/search", params={"q": "삼성전자"})
            stock_id = search.json()[0]["id"]

            # Create discussion
            create = await c.post(
                f"/api/stocks/{stock_id}/discussions",
                json={"content": "삼성전자 실적 어떨까요?"},
                headers=headers,
            )
            assert create.status_code == 201
            disc_id = create.json()["id"]

            # List discussions
            disc_list = await c.get(f"/api/stocks/{stock_id}/discussions", headers=headers)
            assert disc_list.status_code == 200
            assert len(disc_list.json()) >= 1

            # Add comment
            comment = await c.post(
                f"/api/discussions/{disc_id}/comments",
                json={"content": "저도 궁금합니다"},
                headers=headers,
            )
            assert comment.status_code == 201

            # List comments
            comments = await c.get(f"/api/discussions/{disc_id}/comments", headers=headers)
            assert comments.status_code == 200
            assert len(comments.json()) >= 1

            # Update discussion
            update = await c.put(
                f"/api/discussions/{disc_id}",
                json={"content": "삼성전자 4분기 실적 전망?"},
                headers=headers,
            )
            assert update.status_code == 200
            assert "4분기" in update.json()["content"]

            # Delete discussion (cascades comments)
            delete = await c.delete(f"/api/discussions/{disc_id}", headers=headers)
            assert delete.status_code == 204
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_discussion_unauthorized() -> None:
    """Other users cannot edit/delete another's discussion."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token1 = await _signup_login(c, "author@test.com")
            headers1 = {"Authorization": f"Bearer {token1}"}

            search = await c.get("/api/stocks/search", params={"q": "삼성"})
            stock_id = search.json()[0]["id"]

            create = await c.post(
                f"/api/stocks/{stock_id}/discussions",
                json={"content": "나의 글"},
                headers=headers1,
            )
            disc_id = create.json()["id"]

            token2 = await _signup_login(c, "other@test.com")
            headers2 = {"Authorization": f"Bearer {token2}"}

            # Edit by other → 403
            edit = await c.put(
                f"/api/discussions/{disc_id}",
                json={"content": "해킹"},
                headers=headers2,
            )
            assert edit.status_code == 403

            # Delete by other → 403
            delete = await c.delete(f"/api/discussions/{disc_id}", headers=headers2)
            assert delete.status_code == 403
    finally:
        _teardown()


# --- Scenario 6: Briefing API ---


@pytest.mark.asyncio
async def test_briefing_api() -> None:
    """Briefing API returns data (or empty)."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            # Briefings endpoint (no auth required)
            resp = await c.get("/api/briefings", params={"market": "KR", "limit": 5})
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)

            # Today endpoint
            today = await c.get("/api/briefings/today", params={"market": "KR"})
            assert today.status_code == 200
    finally:
        _teardown()


# --- Scenario 7: News feed API ---


@pytest.mark.asyncio
async def test_news_feed_api() -> None:
    """News feed API requires auth and supports filtering."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            # Unauthenticated → 401
            unauth = await c.get("/api/news")
            assert unauth.status_code in (401, 403)

            # Authenticated
            token = await _signup_login(c, "news@test.com")
            headers = {"Authorization": f"Bearer {token}"}

            resp = await c.get("/api/news", headers=headers)
            assert resp.status_code == 200

            # With importance filter
            filtered = await c.get("/api/news", params={"importance": "high"}, headers=headers)
            assert filtered.status_code == 200

            # Invalid importance → 422
            bad = await c.get("/api/news", params={"importance": "invalid"}, headers=headers)
            assert bad.status_code == 422
    finally:
        _teardown()


# --- Scenario 8: Trending and Popular APIs ---


@pytest.mark.asyncio
async def test_trending_and_popular_apis() -> None:
    """Trending and popular APIs work without auth."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            trending = await c.get("/api/trending")
            assert trending.status_code == 200
            assert isinstance(trending.json(), list)

            popular = await c.get("/api/popular")
            assert popular.status_code == 200
            assert isinstance(popular.json(), list)

            # Market filter
            kr = await c.get("/api/trending", params={"market": "KR"})
            assert kr.status_code == 200

            # Period filter
            weekly = await c.get("/api/trending", params={"period": "weekly"})
            assert weekly.status_code == 200
    finally:
        _teardown()


# --- Scenario 9: Calendar API ---


@pytest.mark.asyncio
async def test_calendar_apis() -> None:
    """Calendar APIs return events."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            # Calendar range query
            today = datetime.now().strftime("%Y-%m-%d")
            end = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            resp = await c.get("/api/calendar", params={
                "start_date": today, "end_date": end,
            })
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)

            # Week endpoint
            week = await c.get("/api/calendar/week")
            assert week.status_code == 200
            assert isinstance(week.json(), list)

            # 90-day limit exceeded → 422
            far_end = (datetime.now() + timedelta(days=100)).strftime("%Y-%m-%d")
            bad = await c.get("/api/calendar", params={
                "start_date": today, "end_date": far_end,
            })
            assert bad.status_code == 422
    finally:
        _teardown()


# --- Scenario 10: Unauthenticated access to protected routes ---


@pytest.mark.asyncio
async def test_unauthenticated_access() -> None:
    """Protected endpoints return 401 without auth."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            endpoints = [
                ("GET", "/api/watchlist"),
                ("GET", "/api/profile"),
                ("GET", "/api/news"),
                ("GET", "/api/me"),
            ]
            for method, url in endpoints:
                resp = await c.request(method, url)
                assert resp.status_code in (401, 403), f"{method} {url} should require auth"
    finally:
        _teardown()


# --- Frontend structure checks ---


def test_landing_page_exists():
    """Landing page should exist with hero section."""
    path = os.path.join(BASE_FE, "app", "page.tsx")
    content = open(path).read()
    assert "급변" in content or "AI" in content or "주가" in content


def test_shared_page_exists():
    """Shared report page should exist."""
    path = os.path.join(BASE_FE, "app", "shared", "[token]", "page.tsx")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "shareApi" in content or "shared" in content


def test_mypage_exists():
    """Mypage should exist with profile."""
    path = os.path.join(BASE_FE, "app", "mypage", "page.tsx")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "profile" in content.lower() or "프로필" in content


def test_calendar_page_exists():
    """Calendar page should exist."""
    path = os.path.join(BASE_FE, "app", "calendar", "page.tsx")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "calendar" in content.lower() or "캘린더" in content


def test_news_page_exists():
    """News page should exist."""
    path = os.path.join(BASE_FE, "app", "news", "page.tsx")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "news" in content.lower() or "뉴스" in content


def test_trending_page_exists():
    """Trending page should exist."""
    path = os.path.join(BASE_FE, "app", "trending", "page.tsx")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "trending" in content.lower() or "트렌딩" in content


def test_briefings_page_exists():
    """Briefings archive page should exist."""
    path = os.path.join(BASE_FE, "app", "briefings", "page.tsx")
    assert os.path.isfile(path)


def test_not_found_page():
    """404 page should exist."""
    path = os.path.join(BASE_FE, "app", "not-found.tsx")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "404" in content


def test_seo_meta_in_layout():
    """Root layout should have SEO metadata."""
    path = os.path.join(BASE_FE, "app", "layout.tsx")
    content = open(path).read()
    assert "oh-my-stock" in content
    assert "metadata" in content


def test_robots_txt():
    """robots.txt should exist in public."""
    path = os.path.join(PUBLIC_FE, "robots.txt")
    assert os.path.isfile(path)


def test_sitemap_xml():
    """sitemap.xml should exist in public."""
    path = os.path.join(PUBLIC_FE, "sitemap.xml")
    assert os.path.isfile(path)


def test_manifest_json():
    """PWA manifest should exist."""
    path = os.path.join(PUBLIC_FE, "manifest.json")
    assert os.path.isfile(path)
    import json
    data = json.loads(open(path).read())
    assert "name" in data
    assert "icons" in data


def test_mobile_nav_component():
    """Mobile bottom navigation should exist."""
    path = os.path.join(BASE_FE, "components", "MobileNav.tsx")
    assert os.path.isfile(path)


def test_global_header_component():
    """Global header should exist."""
    path = os.path.join(BASE_FE, "components", "GlobalHeader.tsx")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "oh-my-stock" in content


def test_footer_component():
    """Footer should exist with disclaimer."""
    path = os.path.join(BASE_FE, "components", "GlobalFooter.tsx")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "투자" in content


def test_discussion_section_component():
    """Discussion section should exist."""
    path = os.path.join(BASE_FE, "components", "DiscussionSection.tsx")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "토론" in content or "discussion" in content.lower()


def test_briefing_card_component():
    """BriefingCard widget should exist."""
    path = os.path.join(BASE_FE, "components", "BriefingCard.tsx")
    assert os.path.isfile(path)


def test_news_widget_component():
    """NewsWidget should exist."""
    path = os.path.join(BASE_FE, "components", "NewsWidget.tsx")
    assert os.path.isfile(path)


def test_trending_widget_component():
    """TrendingWidget should exist."""
    path = os.path.join(BASE_FE, "components", "TrendingWidget.tsx")
    assert os.path.isfile(path)


def test_calendar_widget_component():
    """CalendarWidget should exist."""
    path = os.path.join(BASE_FE, "components", "CalendarWidget.tsx")
    assert os.path.isfile(path)


def test_queries_has_all_apis():
    """queries.ts should have all API modules."""
    path = os.path.join(BASE_FE, "lib", "queries.ts")
    content = open(path).read()
    apis = [
        "briefingsApi", "newsApi", "trendingApi", "calendarApi",
        "discussionsApi", "stocksApi", "shareApi", "profileApi",
    ]
    for api in apis:
        assert api in content, f"{api} not found in queries.ts"
