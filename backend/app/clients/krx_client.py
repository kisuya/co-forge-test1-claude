"""KRX stock price client using PyKRX."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MIN = 0
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MIN = 30
MAX_RETRIES = 1


@dataclass
class StockPrice:
    """Price data for a single stock."""
    code: str
    price: Decimal
    change_pct: float
    volume: int


def is_krx_market_open() -> bool:
    """Check if KRX market is currently open (Mon-Fri, 09:00-15:30 KST)."""
    now = datetime.now(KST)
    if now.weekday() >= 5:
        return False
    open_time = now.replace(
        hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MIN, second=0, microsecond=0,
    )
    close_time = now.replace(
        hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MIN, second=0, microsecond=0,
    )
    return open_time <= now <= close_time


def _fetch_single_price(pykrx_stock: object, date_str: str, code: str) -> StockPrice | None:
    """Fetch price for a single stock code with retry."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            df = pykrx_stock.get_market_ohlcv(date_str, date_str, code)
            if df is not None and not df.empty:
                row = df.iloc[-1]
                price = Decimal(str(int(row["종가"])))
                change_pct = float(row["등락률"]) if "등락률" in row else 0.0
                volume = int(row["거래량"])
                return StockPrice(
                    code=code, price=price,
                    change_pct=change_pct, volume=volume,
                )
            return None
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(
                    "KRX fetch retry for %s (attempt %d): %s",
                    code, attempt + 1, str(e),
                )
            else:
                logger.error(
                    "KRX fetch failed for %s after %d attempts: %s",
                    code, MAX_RETRIES + 1, str(e),
                )
    return None


def fetch_current_prices(codes: list[str]) -> list[StockPrice]:
    """Fetch current prices for given stock codes from KRX/PyKRX.

    During market hours (09:00-15:30 KST), fetches today's data.
    Outside market hours, fetches the most recent trading day's data.
    """
    try:
        from pykrx import stock as pykrx_stock
    except ImportError:
        logger.warning("pykrx not installed, skipping KRX price fetch")
        return []

    today = datetime.now(KST).strftime("%Y%m%d")
    results: list[StockPrice] = []

    for code in codes:
        price = _fetch_single_price(pykrx_stock, today, code)
        if price is not None:
            results.append(price)

    logger.info(
        "KRX price fetch complete: %d/%d codes succeeded",
        len(results), len(codes),
    )
    return results
