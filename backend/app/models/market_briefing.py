from __future__ import annotations

from datetime import datetime

from sqlalchemy import Date, DateTime, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class MarketBriefing(Base):
    __tablename__ = "market_briefings"
    __table_args__ = (
        UniqueConstraint("market", "date", name="uq_briefing_market_date"),
        Index("ix_briefings_market_date", "market", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False)  # 'KR' or 'US'
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
