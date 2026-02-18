"""Service for sector-based analysis of related stocks."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.report import PriceSnapshot
from app.models.stock import Stock


@dataclass
class RelatedStockChange:
    """A stock in the same sector with its recent change."""
    name: str
    code: str
    change_pct: float


@dataclass
class SectorImpact:
    """Sector impact analysis result."""
    sector: str
    related_stocks: list[RelatedStockChange]
    correlation_note: str


def get_sector_impact(
    db: Session,
    stock_id: str,
    max_related: int = 10,
    lookback_hours: int = 24,
) -> SectorImpact | None:
    """Find same-sector stocks and their recent price changes.

    Returns None if stock has no sector or no related stocks found.
    """
    import uuid as uuid_mod
    sid = uuid_mod.UUID(stock_id) if isinstance(stock_id, str) else stock_id

    stock = db.execute(
        select(Stock).where(Stock.id == sid)
    ).scalar_one_or_none()

    if not stock or not stock.sector:
        return None

    # Find other stocks in the same sector
    related_query = (
        select(Stock)
        .where(
            Stock.sector == stock.sector,
            Stock.id != sid,
        )
        .limit(max_related)
    )
    related_stocks = list(db.execute(related_query).scalars().all())

    if not related_stocks:
        return None

    cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)

    # For each related stock, get the most recent price snapshot
    results: list[RelatedStockChange] = []
    for rs in related_stocks:
        latest_snap = db.execute(
            select(PriceSnapshot)
            .where(
                PriceSnapshot.stock_id == rs.id,
                PriceSnapshot.captured_at >= cutoff,
            )
            .order_by(PriceSnapshot.captured_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        if latest_snap:
            results.append(RelatedStockChange(
                name=rs.name,
                code=rs.code,
                change_pct=round(latest_snap.change_pct, 2),
            ))

    if not results:
        return None

    # Calculate correlation note
    up_count = sum(1 for r in results if r.change_pct > 0)
    down_count = sum(1 for r in results if r.change_pct < 0)
    total = len(results)

    if up_count > total * 0.6:
        note = f"같은 섹터({stock.sector}) 종목 {total}개 중 {up_count}개가 동반 상승"
    elif down_count > total * 0.6:
        note = f"같은 섹터({stock.sector}) 종목 {total}개 중 {down_count}개가 동반 하락"
    else:
        note = f"같은 섹터({stock.sector}) 종목 {total}개 — 혼조세"

    return SectorImpact(
        sector=stock.sector,
        related_stocks=results,
        correlation_note=note,
    )
