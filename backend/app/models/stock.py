from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name_kr: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    market: Mapped[str] = mapped_column(String(10), nullable=False, default="KRX")
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)

    price_snapshots: Mapped[list["PriceSnapshot"]] = relationship(  # noqa: F821
        back_populates="stock", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(  # noqa: F821
        back_populates="stock", cascade="all, delete-orphan"
    )
    watchlists: Mapped[list["Watchlist"]] = relationship(  # noqa: F821
        back_populates="stock", cascade="all, delete-orphan"
    )
