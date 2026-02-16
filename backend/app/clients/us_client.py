"""US stock price client using yfinance."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)

RATE_LIMIT_DELAY = 0.1  # 100ms between yfinance calls


@dataclass
class USStockPrice:
    """Price data for a US stock."""

    code: str
    price: Decimal
    change_pct: float
    volume: int


def fetch_us_prices(codes: list[str]) -> list[USStockPrice]:
    """Fetch current prices for US stock codes using yfinance.

    Skips individual failures and respects rate limiting (100ms delay).
    """
    try:
        import yfinance as yf
    except ImportError:
        logger.warning("yfinance not installed, skipping US price fetch")
        return []

    results: list[USStockPrice] = []
    for code in codes:
        try:
            ticker = yf.Ticker(code)
            info = ticker.fast_info
            price = Decimal(str(round(info.last_price, 2)))
            prev = info.previous_close
            change_pct = round(((float(price) - prev) / prev) * 100, 2) if prev else 0.0
            volume = int(info.last_volume or 0)
            results.append(USStockPrice(
                code=code, price=price,
                change_pct=change_pct, volume=volume,
            ))
        except Exception:
            logger.warning("Failed to fetch price for %s, skipping", code)
            continue
        time.sleep(RATE_LIMIT_DELAY)

    return results
