from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.krx_client import StockPrice, fetch_current_prices
from app.models.report import PriceSnapshot
from app.models.stock import Stock


def collect_prices(db: Session, fetch_fn: object | None = None) -> int:
    """Collect current prices for all stocks in DB.

    Args:
        db: Database session.
        fetch_fn: Optional override for price fetching (for testing).

    Returns:
        Number of price snapshots saved.
    """
    stocks = db.execute(select(Stock)).scalars().all()
    if not stocks:
        return 0

    codes = [s.code for s in stocks]
    code_to_stock = {s.code: s for s in stocks}

    if fetch_fn is not None:
        prices: list[StockPrice] = fetch_fn(codes)
    else:
        prices = fetch_current_prices(codes)

    count = 0
    for p in prices:
        stock = code_to_stock.get(p.code)
        if stock is None:
            continue
        snapshot = PriceSnapshot(
            stock_id=stock.id,
            price=p.price,
            change_pct=p.change_pct,
            volume=p.volume,
        )
        db.add(snapshot)
        count += 1

    db.commit()
    return count
