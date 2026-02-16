from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class StockPrice:
    """Price data for a single stock."""
    code: str
    price: Decimal
    change_pct: float
    volume: int


def fetch_current_prices(codes: list[str]) -> list[StockPrice]:
    """Fetch current prices for given stock codes from KRX/PyKRX.

    In production, this calls pykrx. For testing, this is mocked.
    """
    try:
        from pykrx import stock as pykrx_stock
        from datetime import datetime

        today = datetime.now().strftime("%Y%m%d")
        results = []
        for code in codes:
            try:
                df = pykrx_stock.get_market_ohlcv(today, today, code)
                if not df.empty:
                    row = df.iloc[-1]
                    price = Decimal(str(int(row["종가"])))
                    change_pct = float(row["등락률"]) if "등락률" in row else 0.0
                    volume = int(row["거래량"])
                    results.append(StockPrice(
                        code=code, price=price,
                        change_pct=change_pct, volume=volume,
                    ))
            except Exception:
                continue
        return results
    except ImportError:
        return []
