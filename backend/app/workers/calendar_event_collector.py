"""Collect calendar events for economic/earnings/central bank schedules (calendar-001).

Seed data for known fixed schedules (FOMC, BOK rate decisions) and
collect earnings dates for watchlisted stocks.
"""
from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.calendar_event import CalendarEvent
from app.models.stock import Stock
from app.models.watchlist import Watchlist

logger = logging.getLogger(__name__)

# --- Seed data: known economic calendar events ---

SEED_EVENTS_2026: list[dict] = [
    # FOMC meetings (US)
    {"event_type": "central_bank", "title": "FOMC 금리 결정", "event_date": date(2026, 1, 28), "market": "US", "source": "Federal Reserve"},
    {"event_type": "central_bank", "title": "FOMC 금리 결정", "event_date": date(2026, 3, 18), "market": "US", "source": "Federal Reserve"},
    {"event_type": "central_bank", "title": "FOMC 금리 결정", "event_date": date(2026, 5, 6), "market": "US", "source": "Federal Reserve"},
    {"event_type": "central_bank", "title": "FOMC 금리 결정", "event_date": date(2026, 6, 17), "market": "US", "source": "Federal Reserve"},
    {"event_type": "central_bank", "title": "FOMC 금리 결정", "event_date": date(2026, 7, 29), "market": "US", "source": "Federal Reserve"},
    {"event_type": "central_bank", "title": "FOMC 금리 결정", "event_date": date(2026, 9, 16), "market": "US", "source": "Federal Reserve"},
    {"event_type": "central_bank", "title": "FOMC 금리 결정", "event_date": date(2026, 11, 4), "market": "US", "source": "Federal Reserve"},
    {"event_type": "central_bank", "title": "FOMC 금리 결정", "event_date": date(2026, 12, 16), "market": "US", "source": "Federal Reserve"},
    # BOK (Bank of Korea) rate decisions
    {"event_type": "central_bank", "title": "한국은행 금통위", "event_date": date(2026, 1, 16), "market": "KR", "source": "한국은행"},
    {"event_type": "central_bank", "title": "한국은행 금통위", "event_date": date(2026, 2, 27), "market": "KR", "source": "한국은행"},
    {"event_type": "central_bank", "title": "한국은행 금통위", "event_date": date(2026, 4, 10), "market": "KR", "source": "한국은행"},
    {"event_type": "central_bank", "title": "한국은행 금통위", "event_date": date(2026, 5, 28), "market": "KR", "source": "한국은행"},
    {"event_type": "central_bank", "title": "한국은행 금통위", "event_date": date(2026, 7, 10), "market": "KR", "source": "한국은행"},
    {"event_type": "central_bank", "title": "한국은행 금통위", "event_date": date(2026, 8, 28), "market": "KR", "source": "한국은행"},
    {"event_type": "central_bank", "title": "한국은행 금통위", "event_date": date(2026, 10, 16), "market": "KR", "source": "한국은행"},
    {"event_type": "central_bank", "title": "한국은행 금통위", "event_date": date(2026, 11, 27), "market": "KR", "source": "한국은행"},
    # Major US economic indicators
    {"event_type": "economic", "title": "미국 CPI 발표", "event_date": date(2026, 1, 14), "market": "US", "source": "BLS"},
    {"event_type": "economic", "title": "미국 CPI 발표", "event_date": date(2026, 2, 11), "market": "US", "source": "BLS"},
    {"event_type": "economic", "title": "미국 CPI 발표", "event_date": date(2026, 3, 11), "market": "US", "source": "BLS"},
    {"event_type": "economic", "title": "미국 고용보고서", "event_date": date(2026, 1, 9), "market": "US", "source": "BLS"},
    {"event_type": "economic", "title": "미국 고용보고서", "event_date": date(2026, 2, 6), "market": "US", "source": "BLS"},
    {"event_type": "economic", "title": "미국 고용보고서", "event_date": date(2026, 3, 6), "market": "US", "source": "BLS"},
]


def seed_calendar_events(db: Session) -> int:
    """Seed known calendar events. Skip duplicates by (title, event_date, market).

    Returns number of newly created events.
    """
    created = 0
    for evt in SEED_EVENTS_2026:
        existing = db.execute(
            select(CalendarEvent).where(
                CalendarEvent.title == evt["title"],
                CalendarEvent.event_date == evt["event_date"],
                CalendarEvent.market == evt["market"],
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue

        event = CalendarEvent(
            event_type=evt["event_type"],
            title=evt["title"],
            event_date=evt["event_date"],
            market=evt["market"],
            source=evt["source"],
        )
        db.add(event)
        created += 1

    if created:
        db.commit()
        logger.info("Seeded %d calendar events", created)

    return created


def _get_tracked_stock_ids(db: Session) -> list:
    """Return stock IDs that are tracked by at least 1 user."""
    from sqlalchemy import func as sqlfunc

    subq = (
        select(Watchlist.stock_id)
        .group_by(Watchlist.stock_id)
        .having(sqlfunc.count(Watchlist.user_id) >= 1)
        .subquery()
    )
    return [
        row[0]
        for row in db.execute(select(subq.c.stock_id)).all()
    ]


def collect_earnings_events(
    db: Session,
    *,
    fetch_fn: object | None = None,
) -> list[CalendarEvent]:
    """Collect earnings announcement dates for watchlisted stocks.

    Args:
        db: Database session.
        fetch_fn: Override for earnings data fetching (for testing).

    Returns:
        List of newly created CalendarEvent entries.
    """
    tracked_ids = _get_tracked_stock_ids(db)
    if not tracked_ids:
        logger.info("No tracked stocks for earnings collection")
        return []

    stocks = list(
        db.execute(
            select(Stock).where(Stock.id.in_(tracked_ids))
        ).scalars().all()
    )

    created: list[CalendarEvent] = []
    for stock in stocks:
        if fetch_fn:
            raw_events = fetch_fn(stock)
        else:
            raw_events = _fetch_earnings_dates(stock)

        for raw in raw_events:
            evt_date = raw.get("event_date")
            if evt_date is None:
                continue

            if isinstance(evt_date, str):
                try:
                    evt_date = date.fromisoformat(evt_date)
                except (ValueError, TypeError):
                    continue

            # Dedup: same stock + same date + earnings type
            existing = db.execute(
                select(CalendarEvent).where(
                    CalendarEvent.stock_id == stock.id,
                    CalendarEvent.event_date == evt_date,
                    CalendarEvent.event_type == "earnings",
                )
            ).scalar_one_or_none()
            if existing is not None:
                continue

            is_korean = stock.market == "KRX"
            event = CalendarEvent(
                event_type="earnings",
                title=raw.get("title", f"{stock.name} 실적 발표"),
                description=raw.get("description"),
                event_date=evt_date,
                market="KR" if is_korean else "US",
                stock_id=stock.id,
                source=raw.get("source", "earnings_calendar"),
            )
            db.add(event)
            created.append(event)

    if created:
        db.commit()
        logger.info("Collected %d earnings events", len(created))

    return created


def _fetch_earnings_dates(stock: Stock) -> list[dict]:
    """Fetch earnings dates for a stock from external sources.

    In production this would call an earnings calendar API.
    Returns empty list when no API is configured.
    """
    return []


def collect_calendar_events(
    db: Session,
    *,
    fetch_fn: object | None = None,
) -> dict:
    """Main collection function: seed + collect earnings.

    Returns summary dict.
    """
    seeded = seed_calendar_events(db)
    earnings = collect_earnings_events(db, fetch_fn=fetch_fn)

    return {
        "seeded": seeded,
        "earnings_collected": len(earnings),
    }


# Celery task — guarded behind try/except for environments without celery
try:
    from app.workers.celery_app import celery
    from app.db.database import get_session_factory

    @celery.task(name="collect_calendar_events_task", bind=True, max_retries=0)
    def collect_calendar_events_task(self) -> dict:
        """Celery periodic task: collect calendar events (daily)."""
        settings = get_settings()
        factory = get_session_factory(settings.database_url)
        session = factory()
        try:
            result = collect_calendar_events(session)
            return {"status": "ok", **result}
        except Exception as exc:
            logger.exception("collect_calendar_events_task failed: %s", exc)
            return {"status": "error", "error": str(exc)}
        finally:
            session.close()

except ImportError:
    collect_calendar_events_task = None  # type: ignore[assignment]
