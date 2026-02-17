from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.sanitize import strip_html_tags
from app.services.stock_service import search_stocks

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


class StockResponse(BaseModel):
    id: str
    code: str
    name: str
    market: str
    sector: str | None = None


@router.get("/search", response_model=list[StockResponse])
def search(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    market: str = Query("kr", description="Market filter: kr, us, or all"),
    db: Session = Depends(get_db),
) -> Any:
    """Search stocks by name or code, filtered by market."""
    q = strip_html_tags(q)
    stocks = search_stocks(db, q, market=market)
    return [
        StockResponse(
            id=str(s.id), code=s.code, name=s.name,
            market=s.market, sector=s.sector,
        )
        for s in stocks
    ]
