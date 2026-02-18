"""US stock price client using yfinance."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)

RATE_LIMIT_DELAY = 0.1  # 100ms between yfinance calls
MAX_RETRIES = 1


@dataclass
class USStockPrice:
    """Price data for a US stock."""

    code: str
    price: Decimal
    change_pct: float
    volume: int


def _fetch_single_us_price(yf_module: object, code: str) -> USStockPrice | None:
    """Fetch price for a single US stock code with retry."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            ticker = yf_module.Ticker(code)
            info = ticker.fast_info
            price = Decimal(str(round(info.last_price, 2)))
            prev = info.previous_close
            change_pct = round(((float(price) - prev) / prev) * 100, 2) if prev else 0.0
            volume = int(info.last_volume or 0)
            return USStockPrice(
                code=code, price=price,
                change_pct=change_pct, volume=volume,
            )
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(
                    "US fetch retry for %s (attempt %d): %s",
                    code, attempt + 1, str(e),
                )
            else:
                logger.error(
                    "US fetch failed for %s after %d attempts: %s",
                    code, MAX_RETRIES + 1, str(e),
                )
    return None


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
        price = _fetch_single_us_price(yf, code)
        if price is not None:
            results.append(price)
        time.sleep(RATE_LIMIT_DELAY)

    logger.info(
        "US price fetch complete: %d/%d codes succeeded",
        len(results), len(codes),
    )
    return results
