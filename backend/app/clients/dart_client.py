from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import httpx

from app.config import get_settings


@dataclass
class Disclosure:
    """A single DART disclosure item."""
    title: str
    url: str
    published_at: datetime | None = None


def fetch_disclosures(stock_code: str, days: int = 7) -> list[Disclosure]:
    """Fetch recent disclosures from DART OpenAPI for a given stock.

    In production, calls DART API. For testing, this is mocked.
    """
    settings = get_settings()
    if not settings.dart_api_key:
        return []

    try:
        resp = httpx.get(
            "https://opendart.fss.or.kr/api/list.json",
            params={
                "crtfc_key": settings.dart_api_key,
                "corp_code": stock_code,
                "page_count": "10",
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("list", []):
            results.append(Disclosure(
                title=item.get("report_nm", ""),
                url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.get('rcept_no', '')}",
                published_at=None,
            ))
        return results
    except Exception:
        return []
