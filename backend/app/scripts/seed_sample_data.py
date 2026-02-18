"""Seed sample data for development/testing.

Idempotent: safe to run multiple times. Uses UPSERT semantics
(deletes existing sample data, then re-inserts).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import bcrypt
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.calendar_event import CalendarEvent
from app.models.discussion import Discussion, DiscussionComment
from app.models.market_briefing import MarketBriefing
from app.models.news_article import NewsArticle
from app.models.report import PriceSnapshot, Report
from app.models.shared_report import SharedReport
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks, seed_us_stocks

SAMPLE_EMAILS = ["test@example.com", "investor@example.com"]
SAMPLE_PASSWORD = "testpass123"


def _hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _days_ago(n: int) -> datetime:
    return _now() - timedelta(days=n)


def _date_ago(n: int) -> date:
    return (datetime.now(timezone.utc) - timedelta(days=n)).date()


SEED_REPORT_SUMMARY_PREFIX = "[SEED] "
SEED_NEWS_URL_PREFIX = "https://example.com/news/"


def clean_sample_data(db: Session) -> None:
    """Remove existing sample data. Idempotent — safe to call multiple times."""
    # Delete shared reports for seed reports first
    seed_reports = db.execute(
        select(Report).where(Report.summary.like(f"{SEED_REPORT_SUMMARY_PREFIX}%"))
    ).scalars().all()
    for report in seed_reports:
        shared = db.execute(
            select(SharedReport).where(SharedReport.report_id == report.id)
        ).scalars().all()
        for s in shared:
            db.delete(s)

    # Delete seed reports (cascades to report_sources)
    for report in seed_reports:
        db.delete(report)

    # Delete seed price snapshots — delete all with volume in known set
    # (simpler: delete any snapshots tied to seed data volumes)
    db.execute(
        PriceSnapshot.__table__.delete().where(
            PriceSnapshot.volume.in_([
                15000000, 12000000, 18000000, 8000000, 6000000, 9000000,
                2000000, 1500000, 2200000, 5000000, 4500000, 6000000,
                3000000, 2800000, 3500000,
            ])
        )
    )

    # Delete users (cascades to watchlists, discussions, comments, push subs)
    for email in SAMPLE_EMAILS:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user:
            db.delete(user)

    # Delete seed news articles (identified by URL pattern)
    db.execute(
        NewsArticle.__table__.delete().where(
            NewsArticle.url.like(f"{SEED_NEWS_URL_PREFIX}%")
        )
    )

    # Delete seed briefings
    for briefing in db.execute(select(MarketBriefing)).scalars().all():
        if briefing.content and isinstance(briefing.content, dict):
            highlights = briefing.content.get("highlights", [])
            if "반도체 섹터 강세" in highlights:
                db.delete(briefing)

    # Delete seed calendar events (source = "seed_data")
    db.execute(
        CalendarEvent.__table__.delete().where(
            CalendarEvent.source == "seed_data"
        )
    )

    db.commit()


def seed_users(db: Session) -> tuple[User, User]:
    """Create 2 test users."""
    pw_hash = _hash_pw(SAMPLE_PASSWORD)

    user1 = User(
        email="test@example.com",
        password_hash=pw_hash,
        nickname="testuser",
        settings={"theme": "light", "language": "ko"},
    )
    user2 = User(
        email="investor@example.com",
        password_hash=pw_hash,
        nickname="investor",
        settings={"theme": "dark", "language": "ko"},
    )
    db.add(user1)
    db.commit()
    db.add(user2)
    db.commit()
    return user1, user2


def seed_watchlists(db: Session, user1: User, user2: User) -> list[Watchlist]:
    """Create 8 watchlist entries across 2 users."""
    stocks = db.execute(select(Stock).limit(8)).scalars().all()
    if len(stocks) < 8:
        raise ValueError(f"Need at least 8 stocks, found {len(stocks)}. Run seed_stocks first.")

    watchlists = []
    # User1 gets 5 stocks
    for i, stock in enumerate(stocks[:5]):
        w = Watchlist(
            user_id=user1.id,
            stock_id=stock.id,
            threshold=3.0 + i * 0.5,
            alert_enabled=True,
        )
        watchlists.append(w)

    # User2 gets 3 stocks
    for i, stock in enumerate(stocks[3:6]):
        w = Watchlist(
            user_id=user2.id,
            stock_id=stock.id,
            threshold=5.0,
            alert_enabled=i < 2,
        )
        watchlists.append(w)

    db.add_all(watchlists)
    db.commit()
    return watchlists


def seed_price_snapshots(db: Session) -> list[PriceSnapshot]:
    """Create 15 price snapshots across multiple stocks."""
    stocks = db.execute(select(Stock).limit(5)).scalars().all()
    snapshots = []

    prices_data = [
        (0, 72000, -5.2, 15000000),
        (0, 73500, 2.1, 12000000),
        (0, 71800, -2.3, 18000000),
        (1, 128000, -7.8, 8000000),
        (1, 130000, 1.6, 6000000),
        (1, 126500, -2.7, 9000000),
        (2, 380000, 3.5, 2000000),
        (2, 375000, -1.3, 1500000),
        (2, 382000, 1.9, 2200000),
        (3, 52000, -4.1, 5000000),
        (3, 53500, 2.9, 4500000),
        (3, 51000, -4.7, 6000000),
        (4, 215000, 1.2, 3000000),
        (4, 212000, -1.4, 2800000),
        (4, 218000, 2.8, 3500000),
    ]

    for stock_idx, price, change, volume in prices_data:
        snap = PriceSnapshot(
            stock_id=stocks[stock_idx].id,
            price=Decimal(str(price)),
            change_pct=change,
            volume=volume,
            captured_at=_days_ago(len(snapshots) % 7),
        )
        snapshots.append(snap)

    db.add_all(snapshots)
    db.commit()
    return snapshots


def seed_reports(db: Session) -> list[Report]:
    """Create 7 reports with analysis JSON."""
    stocks = db.execute(select(Stock).limit(4)).scalars().all()
    reports = []

    analysis_templates = [
        {
            "causes": [
                {"title": "실적 부진", "description": "3분기 영업이익 시장 예상치 하회", "confidence": 0.9},
                {"title": "반도체 수요 둔화", "description": "글로벌 PC/스마트폰 수요 감소", "confidence": 0.7},
            ],
            "similar_cases": [
                {"date": "2024-01-15", "description": "삼성전자 4분기 실적 쇼크", "change_pct": -6.2},
            ],
            "summary": "3분기 실적이 시장 기대에 미치지 못하며 급락",
        },
        {
            "causes": [
                {"title": "AI 반도체 수요 급증", "description": "HBM3E 수주 확대", "confidence": 0.95},
            ],
            "similar_cases": [
                {"date": "2024-03-20", "description": "엔비디아 실적 서프라이즈", "change_pct": 8.5},
            ],
            "summary": "AI 반도체 HBM3E 대량 수주 소식에 급등",
        },
        {
            "causes": [
                {"title": "광고 수익 감소", "description": "디지털 광고 시장 경쟁 심화", "confidence": 0.8},
                {"title": "규제 리스크", "description": "공정위 조사 소식", "confidence": 0.6},
            ],
            "similar_cases": [],
            "summary": "광고 수익 둔화 우려 및 규제 이슈",
        },
    ]

    for i in range(7):
        stock = stocks[i % len(stocks)]
        analysis = analysis_templates[i % len(analysis_templates)]
        status = "completed" if i < 5 else "pending"

        report = Report(
            stock_id=stock.id,
            trigger_price=Decimal(str(70000 + i * 5000)),
            trigger_change_pct=-5.0 + i * 1.5,
            summary=f"{SEED_REPORT_SUMMARY_PREFIX}{analysis['summary']}",
            analysis=analysis,
            status=status,
            created_at=_days_ago(i),
            completed_at=_days_ago(i) if status == "completed" else None,
        )
        reports.append(report)

    db.add_all(reports)
    db.commit()
    return reports


def seed_news(db: Session) -> list[NewsArticle]:
    """Create 12 news articles."""
    stocks = db.execute(select(Stock).limit(4)).scalars().all()
    articles = []

    news_data = [
        ("삼성전자, 3분기 영업이익 시장 예상 하회", "한국경제", "high"),
        ("SK하이닉스, HBM3E 대규모 수주 성공", "매일경제", "high"),
        ("NAVER, AI 검색 서비스 본격 출시", "조선비즈", "medium"),
        ("카카오, 신규 핀테크 서비스 런칭 예정", "한국경제", "medium"),
        ("반도체 업황 회복 시그널 포착", "서울경제", "high"),
        ("AI 테마주 일제히 상승세", "매경이코노미", "medium"),
        ("외국인 투자자 순매수 전환", "이데일리", "low"),
        ("금리 인하 기대감 확산", "파이낸셜뉴스", "medium"),
        ("삼성전자 자사주 매입 프로그램 발표", "한국경제", "high"),
        ("SK하이닉스 신공장 착공", "매일경제", "medium"),
        ("IT 섹터 실적 시즌 본격 시작", "조선비즈", "medium"),
        ("글로벌 증시 동반 상승", "서울경제", "low"),
    ]

    for i, (title, source, importance) in enumerate(news_data):
        stock = stocks[i % len(stocks)] if i < 8 else None
        article = NewsArticle(
            stock_id=stock.id if stock else None,
            title=title,
            url=f"https://example.com/news/{i+1}",
            source=source,
            published_at=_days_ago(i),
            content_summary=f"{title}에 대한 상세 분석 내용입니다.",
            importance=importance,
        )
        articles.append(article)

    db.add_all(articles)
    db.commit()
    return articles


def seed_briefings(db: Session) -> list[MarketBriefing]:
    """Create 3 market briefings."""
    briefings = []

    for i, market in enumerate(["KR", "US", "KR"]):
        briefing = MarketBriefing(
            market=market,
            date=_date_ago(i),
            content={
                "title": f"{'한국' if market == 'KR' else '미국'} 시장 브리핑",
                "summary": f"{'코스피' if market == 'KR' else 'S&P 500'} 주요 변동 요약",
                "highlights": [
                    "반도체 섹터 강세",
                    "금리 인하 기대감",
                    "외국인 순매수 전환",
                ],
                "market_sentiment": "neutral" if i > 0 else "positive",
            },
        )
        briefings.append(briefing)

    db.add_all(briefings)
    db.commit()
    return briefings


def seed_calendar_events(db: Session) -> list[CalendarEvent]:
    """Create 9 calendar events."""
    stocks = db.execute(select(Stock).limit(3)).scalars().all()
    events = []

    events_data = [
        ("earnings", "삼성전자 3분기 실적 발표", "KR", 0, 7),
        ("earnings", "SK하이닉스 3분기 실적 발표", "KR", 1, 10),
        ("economic", "한국은행 기준금리 결정", "KR", None, 14),
        ("central_bank", "미국 FOMC 금리 결정", "US", None, 21),
        ("dividend", "삼성전자 배당금 지급일", "KR", 0, 30),
        ("earnings", "NAVER 3분기 실적 발표", "KR", 2, 12),
        ("economic", "미국 고용 지표 발표", "US", None, 5),
        ("economic", "한국 CPI 발표", "KR", None, 3),
        ("central_bank", "ECB 금리 결정", "GLOBAL", None, 18),
    ]

    for event_type, title, market, stock_idx, days_ahead in events_data:
        ev = CalendarEvent(
            event_type=event_type,
            title=title,
            description=f"{title} 예정",
            event_date=(datetime.now(timezone.utc) + timedelta(days=days_ahead)).date(),
            market=market,
            stock_id=stocks[stock_idx].id if stock_idx is not None else None,
            source="seed_data",
        )
        events.append(ev)

    db.add_all(events)
    db.commit()
    return events


def seed_discussions(db: Session, user1: User, user2: User) -> tuple[list[Discussion], list[DiscussionComment]]:
    """Create 6 discussions and 5 comments."""
    stocks = db.execute(select(Stock).limit(3)).scalars().all()

    discussions_data = [
        (0, user1, "삼성전자 3분기 실적, 어떻게 보시나요?"),
        (0, user2, "반도체 사이클 바닥은 지났을까요?"),
        (1, user1, "SK하이닉스 HBM3E 수주, 장기적으로 긍정적?"),
        (1, user2, "메모리 반도체 업황 전망"),
        (2, user1, "NAVER AI 검색 서비스 기대되네요"),
        (2, user2, "카카오 vs 네이버, 어디에 투자할까?"),
    ]

    discussions = []
    for stock_idx, user, content in discussions_data:
        d = Discussion(
            stock_id=stocks[stock_idx].id,
            user_id=user.id,
            content=content,
            created_at=_days_ago(len(discussions)),
        )
        discussions.append(d)

    db.add_all(discussions)
    db.commit()

    comments_data = [
        (0, user2, "저도 실적이 걱정됩니다. 하반기 회복 가능할까요?"),
        (0, user1, "HBM 매출 비중이 올라가면서 개선될 것 같습니다"),
        (1, user1, "아직 불확실하지만 재고 조정은 거의 끝난 듯합니다"),
        (2, user2, "HBM3E 계약 단가가 높아서 마진 개선 기대됩니다"),
        (4, user2, "AI 검색이 트래픽에 어떤 영향을 줄지 궁금합니다"),
    ]

    comments = []
    for disc_idx, user, content in comments_data:
        c = DiscussionComment(
            discussion_id=discussions[disc_idx].id,
            user_id=user.id,
            content=content,
            created_at=_days_ago(len(comments)),
        )
        comments.append(c)

    db.add_all(comments)
    db.commit()
    return discussions, comments


def seed_shared_report(db: Session, user1: User, reports: list[Report]) -> SharedReport:
    """Create 1 shared report."""
    if not reports:
        raise ValueError("Need at least 1 report to create a shared report")

    shared = SharedReport(
        report_id=reports[0].id,
        share_token=str(uuid.uuid4()),
        created_by=user1.id,
        expires_at=_now() + timedelta(days=30),
    )
    db.add(shared)
    db.commit()
    return shared


def run_seed(database_url: str) -> dict[str, int]:
    """Run the complete seed process. Returns counts of seeded entities."""
    create_tables(database_url)
    factory = get_session_factory(database_url)
    db = factory()

    try:
        # Seed stocks first (dependency for everything else)
        seed_stocks(db)
        seed_us_stocks(db)

        # Clean existing sample data (idempotent)
        clean_sample_data(db)

        # Seed all entities
        user1, user2 = seed_users(db)
        watchlists = seed_watchlists(db, user1, user2)
        snapshots = seed_price_snapshots(db)
        reports = seed_reports(db)
        news = seed_news(db)
        briefings = seed_briefings(db)
        events = seed_calendar_events(db)
        discussions, comments = seed_discussions(db, user1, user2)
        shared = seed_shared_report(db, user1, reports)

        return {
            "users": 2,
            "watchlists": len(watchlists),
            "price_snapshots": len(snapshots),
            "reports": len(reports),
            "news_articles": len(news),
            "market_briefings": len(briefings),
            "calendar_events": len(events),
            "discussions": len(discussions),
            "discussion_comments": len(comments),
            "shared_reports": 1,
        }
    finally:
        db.close()


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    db_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/ohmystock")
    print(f"Seeding database: {db_url}")
    counts = run_seed(db_url)
    print("Seed complete:")
    for entity, count in counts.items():
        print(f"  {entity}: {count}")
