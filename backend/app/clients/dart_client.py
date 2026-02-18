"""DART disclosure client for Korean stock disclosures."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

DART_API_BASE = "https://opendart.fss.or.kr/api/list.json"
MAX_RETRIES = 1
# Disclosure types to filter (주요사항보고, 실적, 지분변동 etc.)
DISCLOSURE_TYPE_FILTERS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J")


@dataclass
class Disclosure:
    """A single DART disclosure item."""
    title: str
    url: str
    corp_code: str = ""
    published_at: datetime | None = None


def fetch_disclosures(
    stock_code: str,
    days: int = 7,
    api_key: str | None = None,
) -> list[Disclosure]:
    """Fetch recent disclosures from DART OpenAPI for a given stock.

    Args:
        stock_code: Stock code (used as corp_code for DART API).
        days: Number of days to look back.
        api_key: Optional API key override (for testing).

    Returns:
        List of Disclosure objects. Empty list on error or missing API key.
    """
    if api_key is None:
        settings = get_settings()
        api_key = settings.dart_api_key

    if not api_key:
        logger.warning("DART_API_KEY not set, skipping disclosure fetch")
        return []

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = httpx.get(
                DART_API_BASE,
                params={
                    "crtfc_key": api_key,
                    "corp_code": stock_code,
                    "page_count": "20",
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("list", []):
                pub_date = None
                date_str = item.get("rcept_dt", "")
                if date_str and len(date_str) == 8:
                    try:
                        pub_date = datetime.strptime(date_str, "%Y%m%d")
                    except ValueError:
                        pass

                url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.get('rcept_no', '')}"
                results.append(Disclosure(
                    title=item.get("report_nm", ""),
                    url=url,
                    corp_code=stock_code,
                    published_at=pub_date,
                ))

            logger.info(
                "DART fetch complete for %s: %d disclosures",
                stock_code, len(results),
            )
            return results
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(
                    "DART fetch retry for %s (attempt %d): %s",
                    stock_code, attempt + 1, str(e),
                )
            else:
                logger.error(
                    "DART fetch failed for %s after %d attempts: %s",
                    stock_code, MAX_RETRIES + 1, str(e),
                )

    return []
