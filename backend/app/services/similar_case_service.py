"""Service for finding similar historical price movement cases."""
from __future__ import annotations

import uuid as uuid_mod
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report import PriceSnapshot

CHANGE_RANGE = 1.5  # ±1.5%p tolerance
MIN_DAYS_AGO = 30
MAX_RESULTS = 3
DEDUP_DAYS = 2  # ±2 day consecutive event dedup
CHANGE_WEIGHT = 0.6
VOLUME_WEIGHT = 0.4
TREND_1W_DAYS = 5  # 5 trading days
TREND_1M_DAYS = 20  # 20 trading days


@dataclass
class TrendPoint:
    day: int
    change_pct: float


@dataclass
class SimilarCase:
    date: datetime
    change_pct: float
    volume: int
    similarity_score: float


@dataclass
class CaseAftermath:
    """Price aftermath after a historical event."""
    after_1w_pct: float | None  # 1-week return %
    after_1m_pct: float | None  # 1-month return %
    recovery_days: int | None  # days to recover to pre-event price, None if unrecovered


@dataclass
class SimilarCaseWithTrend:
    date: datetime
    change_pct: float
    volume: int
    similarity_score: float
    trend_1w: list[TrendPoint]
    trend_1m: list[TrendPoint]
    data_insufficient: bool = False
    aftermath: CaseAftermath | None = None


def _compute_similarity(
    target_pct: float,
    target_volume: int,
    candidate_pct: float,
    candidate_volume: int,
) -> float:
    change_diff = abs(target_pct - candidate_pct)
    if target_volume > 0 and candidate_volume > 0:
        volume_ratio_diff = abs(1.0 - candidate_volume / target_volume)
    else:
        volume_ratio_diff = 1.0
    return change_diff * CHANGE_WEIGHT + volume_ratio_diff * VOLUME_WEIGHT


def _dedup_consecutive(
    cases: list[tuple[PriceSnapshot, float]],
) -> list[tuple[PriceSnapshot, float]]:
    """Remove consecutive-day duplicates, keeping the best (lowest) score."""
    if not cases:
        return []
    result: list[tuple[PriceSnapshot, float]] = []
    for snap, score in cases:
        is_dup = False
        for existing_snap, existing_score in result:
            day_diff = abs((snap.captured_at - existing_snap.captured_at).days)
            if day_diff <= DEDUP_DAYS:
                is_dup = True
                if score < existing_score:
                    result.remove((existing_snap, existing_score))
                    result.append((snap, score))
                break
        if not is_dup:
            result.append((snap, score))
    return result


def _get_trend_after(
    db: Session,
    stock_id: uuid_mod.UUID,
    event_date: datetime,
    max_days: int,
) -> list[TrendPoint]:
    """Get price trend after an event date as cumulative change_pct."""
    stmt = (
        select(PriceSnapshot)
        .where(
            PriceSnapshot.stock_id == stock_id,
            PriceSnapshot.captured_at > event_date,
        )
        .order_by(PriceSnapshot.captured_at.asc())
        .limit(max_days)
    )
    snapshots = list(db.execute(stmt).scalars().all())
    if not snapshots:
        return []

    base_price = snapshots[0].price
    points: list[TrendPoint] = []
    for i, snap in enumerate(snapshots):
        if base_price > 0:
            cum_pct = float((snap.price - base_price) / base_price * 100)
        else:
            cum_pct = 0.0
        points.append(TrendPoint(day=i + 1, change_pct=round(cum_pct, 2)))
    return points


def _compute_aftermath(
    db: Session,
    stock_id: uuid_mod.UUID,
    event_date: datetime,
    event_price: float,
) -> CaseAftermath | None:
    """Compute price aftermath after an event: 1w/1m returns and recovery days."""
    # Get up to 30 trading days of snapshots after the event
    stmt = (
        select(PriceSnapshot)
        .where(
            PriceSnapshot.stock_id == stock_id,
            PriceSnapshot.captured_at > event_date,
        )
        .order_by(PriceSnapshot.captured_at.asc())
        .limit(30)
    )
    snapshots = list(db.execute(stmt).scalars().all())
    if not snapshots or event_price <= 0:
        return None

    after_1w_pct: float | None = None
    after_1m_pct: float | None = None
    recovery_days: int | None = None

    # Compute 1-week return (5th trading day or last available before that)
    if len(snapshots) >= TREND_1W_DAYS:
        w_price = float(snapshots[TREND_1W_DAYS - 1].price)
        after_1w_pct = round((w_price - event_price) / event_price * 100, 2)
    elif len(snapshots) > 0:
        # Insufficient data for full week
        after_1w_pct = None

    # Compute 1-month return (20th trading day or last available before that)
    if len(snapshots) >= TREND_1M_DAYS:
        m_price = float(snapshots[TREND_1M_DAYS - 1].price)
        after_1m_pct = round((m_price - event_price) / event_price * 100, 2)

    # Find recovery day: first day price >= event_price (for drops) or <= event_price (for rises)
    for i, snap in enumerate(snapshots):
        snap_price = float(snap.price)
        if snap_price >= event_price:
            recovery_days = i + 1
            break

    return CaseAftermath(
        after_1w_pct=after_1w_pct,
        after_1m_pct=after_1m_pct,
        recovery_days=recovery_days,
    )


def get_cases_with_trends(
    db: Session,
    stock_id: str,
    change_pct: float,
    exclude_date: datetime | None = None,
    reference_volume: int = 0,
) -> list[SimilarCaseWithTrend]:
    """Find similar cases and attach 1w/1m price trends + aftermath."""
    cases = find_similar_cases(
        db, stock_id, change_pct, exclude_date, reference_volume,
    )
    sid = uuid_mod.UUID(stock_id) if isinstance(stock_id, str) else stock_id
    results: list[SimilarCaseWithTrend] = []
    for c in cases:
        trend_1w = _get_trend_after(db, sid, c.date, TREND_1W_DAYS)
        trend_1m = _get_trend_after(db, sid, c.date, TREND_1M_DAYS)
        insufficient = len(trend_1w) < TREND_1W_DAYS

        # Get the event price for aftermath calculation
        event_snap = db.execute(
            select(PriceSnapshot)
            .where(
                PriceSnapshot.stock_id == sid,
                PriceSnapshot.captured_at == c.date,
            )
            .limit(1)
        ).scalar_one_or_none()

        aftermath = None
        if event_snap:
            aftermath = _compute_aftermath(
                db, sid, c.date, float(event_snap.price),
            )

        results.append(SimilarCaseWithTrend(
            date=c.date,
            change_pct=c.change_pct,
            volume=c.volume,
            similarity_score=c.similarity_score,
            trend_1w=trend_1w,
            trend_1m=trend_1m,
            data_insufficient=insufficient,
            aftermath=aftermath,
        ))
    return results


def find_similar_cases(
    db: Session,
    stock_id: str,
    change_pct: float,
    exclude_date: datetime | None = None,
    reference_volume: int = 0,
) -> list[SimilarCase]:
    """Find similar historical price movements for a stock.

    Returns up to MAX_RESULTS cases sorted by similarity (lowest score = most similar).
    Returns empty list when data is insufficient (not an error).
    """
    cutoff = datetime.utcnow() - timedelta(days=MIN_DAYS_AGO)
    low = change_pct - CHANGE_RANGE
    high = change_pct + CHANGE_RANGE

    sid = uuid_mod.UUID(stock_id) if isinstance(stock_id, str) else stock_id

    stmt = (
        select(PriceSnapshot)
        .where(
            PriceSnapshot.stock_id == sid,
            PriceSnapshot.change_pct >= low,
            PriceSnapshot.change_pct <= high,
            PriceSnapshot.captured_at < cutoff,
        )
        .order_by(PriceSnapshot.captured_at.desc())
    )

    snapshots = list(db.execute(stmt).scalars().all())

    if exclude_date is not None:
        snapshots = [
            s for s in snapshots
            if abs((s.captured_at - exclude_date).days) > DEDUP_DAYS
        ]

    ref_volume = reference_volume if reference_volume > 0 else 1
    scored = [
        (s, _compute_similarity(change_pct, ref_volume, s.change_pct, s.volume))
        for s in snapshots
    ]

    scored.sort(key=lambda x: x[1])

    deduped = _dedup_consecutive(scored)
    deduped.sort(key=lambda x: x[1])
    top = deduped[:MAX_RESULTS]

    return [
        SimilarCase(
            date=s.captured_at,
            change_pct=s.change_pct,
            volume=s.volume,
            similarity_score=round(score, 4),
        )
        for s, score in top
    ]
