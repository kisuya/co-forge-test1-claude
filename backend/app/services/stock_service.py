from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.stock import Stock

SAMPLE_KRX_STOCKS = [
    ("005930", "삼성전자", "KRX", "전기전자"),
    ("000660", "SK하이닉스", "KRX", "전기전자"),
    ("035420", "NAVER", "KRX", "서비스업"),
    ("035720", "카카오", "KRX", "서비스업"),
    ("005380", "현대차", "KRX", "운수장비"),
    ("051910", "LG화학", "KRX", "화학"),
    ("006400", "삼성SDI", "KRX", "전기전자"),
    ("068270", "셀트리온", "KRX", "의약품"),
    ("028260", "삼성물산", "KRX", "유통업"),
    ("105560", "KB금융", "KRX", "금융업"),
    ("055550", "신한지주", "KRX", "금융업"),
    ("003550", "LG", "KRX", "전기전자"),
    ("017670", "SK텔레콤", "KRX", "통신업"),
    ("034730", "SK", "KRX", "지주회사"),
    ("015760", "한국전력", "KRX", "전기가스"),
    ("032830", "삼성생명", "KRX", "보험"),
    ("003670", "포스코퓨처엠", "KRX", "철강금속"),
    ("066570", "LG전자", "KRX", "전기전자"),
    ("033780", "KT&G", "KRX", "음식료"),
    ("030200", "KT", "KRX", "통신업"),
    ("086790", "하나금융지주", "KRX", "금융업"),
    ("018260", "삼성에스디에스", "KRX", "서비스업"),
    ("316140", "우리금융지주", "KRX", "금융업"),
    ("009150", "삼성전기", "KRX", "전기전자"),
    ("000270", "기아", "KRX", "운수장비"),
    ("012330", "현대모비스", "KRX", "운수장비"),
    ("096770", "SK이노베이션", "KRX", "화학"),
    ("011170", "롯데케미칼", "KRX", "화학"),
    ("034020", "두산에너빌리티", "KRX", "기계"),
    ("010130", "고려아연", "KRX", "비철금속"),
]


def seed_stocks(db: Session) -> int:
    """Seed sample KRX stocks into the database. Returns count of new stocks."""
    count = 0
    for code, name, market, sector in SAMPLE_KRX_STOCKS:
        existing = db.execute(
            select(Stock).where(Stock.code == code)
        ).scalar_one_or_none()
        if existing is None:
            db.add(Stock(code=code, name=name, market=market, sector=sector))
            count += 1
    db.commit()
    return count


def seed_us_stocks(db: Session) -> int:
    """Seed S&P 500 major US stocks. Returns count of new stocks."""
    from app.data.us_stocks import SAMPLE_US_STOCKS

    count = 0
    for code, name, name_kr, market, sector in SAMPLE_US_STOCKS:
        existing = db.execute(
            select(Stock).where(Stock.code == code)
        ).scalar_one_or_none()
        if existing is None:
            db.add(Stock(
                code=code, name=name, name_kr=name_kr,
                market=market, sector=sector,
            ))
            count += 1
    db.commit()
    return count


MARKET_FILTER = {
    "kr": ["KRX"],
    "us": ["NYSE", "NASDAQ"],
    "all": ["KRX", "NYSE", "NASDAQ"],
}


def search_stocks(
    db: Session, query: str, limit: int = 20, market: str = "kr",
) -> list[Stock]:
    """Search stocks by name, name_kr, or code. Case-insensitive partial match."""
    pattern = f"%{query}%"
    markets = MARKET_FILTER.get(market, MARKET_FILTER["kr"])
    stmt = (
        select(Stock)
        .where(
            Stock.market.in_(markets),
            or_(
                Stock.name.ilike(pattern),
                Stock.name_kr.ilike(pattern),
                Stock.code.ilike(pattern),
            ),
        )
        .limit(limit)
    )
    result = db.execute(stmt)
    return list(result.scalars().all())
