from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report import PriceSnapshot, Report
from app.models.stock import Stock
from app.models.watchlist import Watchlist

DEFAULT_THRESHOLD = 3.0


def detect_price_spikes(db: Session) -> list[Report]:
    """Check latest price snapshots for spikes exceeding user thresholds.

    For each watchlist entry, find the latest PriceSnapshot. If the absolute
    change_pct exceeds the user's threshold, create a pending Report.

    Returns list of newly created Reports.
    """
    watchlists = db.execute(select(Watchlist)).scalars().all()
    created_reports: list[Report] = []

    for wl in watchlists:
        threshold = wl.threshold or DEFAULT_THRESHOLD

        latest_snapshot = db.execute(
            select(PriceSnapshot)
            .where(PriceSnapshot.stock_id == wl.stock_id)
            .order_by(PriceSnapshot.captured_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        if latest_snapshot is None:
            continue

        if abs(latest_snapshot.change_pct) < threshold:
            continue

        existing_report = db.execute(
            select(Report).where(
                Report.stock_id == wl.stock_id,
                Report.trigger_price == latest_snapshot.price,
                Report.status.in_(["pending", "generating"]),
            )
        ).scalar_one_or_none()

        if existing_report is not None:
            continue

        report = Report(
            stock_id=wl.stock_id,
            trigger_price=latest_snapshot.price,
            trigger_change_pct=latest_snapshot.change_pct,
            status="pending",
        )
        db.add(report)
        created_reports.append(report)

    db.commit()
    return created_reports
