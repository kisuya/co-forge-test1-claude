from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.dart_client import Disclosure, fetch_disclosures
from app.models.report import Report, ReportSource
from app.models.stock import Stock


@dataclass
class NewsItem:
    """A single news article."""
    title: str
    url: str
    published_at: datetime | None = None


def collect_news_for_report(
    db: Session,
    report: Report,
    disclosure_fn: object | None = None,
    news_fn: object | None = None,
) -> list[ReportSource]:
    """Collect news and disclosures for a pending report.

    Args:
        db: Database session.
        report: Report to collect sources for.
        disclosure_fn: Optional override for disclosure fetching.
        news_fn: Optional override for news fetching.

    Returns:
        List of created ReportSource entries.
    """
    stock = db.execute(
        select(Stock).where(Stock.id == report.stock_id)
    ).scalar_one_or_none()

    if stock is None:
        return []

    sources: list[ReportSource] = []

    if disclosure_fn is not None:
        disclosures: list[Disclosure] = disclosure_fn(stock.code)
    else:
        disclosures = fetch_disclosures(stock.code)

    for d in disclosures:
        src = ReportSource(
            report_id=report.id,
            source_type="disclosure",
            title=d.title,
            url=d.url,
            published_at=d.published_at,
        )
        db.add(src)
        sources.append(src)

    if news_fn is not None:
        news_items: list[NewsItem] = news_fn(stock.name)
        for n in news_items:
            src = ReportSource(
                report_id=report.id,
                source_type="news",
                title=n.title,
                url=n.url,
                published_at=n.published_at,
            )
            db.add(src)
            sources.append(src)

    db.commit()
    return sources
