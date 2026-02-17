"""Celery task for generating AI briefings from collected market data."""
from __future__ import annotations

import json
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_briefing import MarketBriefing

logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")

MAX_TOKENS = 1000


def generate_market_briefing(
    db: Session,
    market: str = "KR",
    target_date: date | None = None,
    generate_fn: object | None = None,
    max_retries: int = 3,
) -> MarketBriefing | None:
    """Generate AI briefing from collected market data.

    Args:
        db: Database session.
        market: 'KR' or 'US'.
        target_date: Date for the briefing. Defaults to today (KST).
        generate_fn: Optional override for AI generation (for testing).
        max_retries: Number of retries on API failure.

    Returns:
        Updated MarketBriefing with AI-generated content, or None.
    """
    if target_date is None:
        target_date = datetime.now(KST).date()

    briefing = db.execute(
        select(MarketBriefing).where(
            MarketBriefing.market == market,
            MarketBriefing.date == target_date,
        )
    ).scalar_one_or_none()

    if briefing is None:
        logger.error("No raw briefing found for %s %s", market, target_date)
        return None

    raw_content = briefing.content
    if raw_content is None:
        logger.error("Briefing content is empty for %s %s", market, target_date)
        return None

    # Skip if already processed (has 'summary' key from AI)
    if raw_content.get("summary") and raw_content.get("key_issues"):
        logger.info("Briefing already processed for %s %s", market, target_date)
        return briefing

    if generate_fn is not None:
        ai_result = generate_fn(raw_content)
    else:
        ai_result = _call_ai(raw_content, max_retries=max_retries)

    if ai_result is None:
        logger.error("AI generation failed for %s %s", market, target_date)
        return None

    # Merge AI result into existing content
    updated_content = {**raw_content}
    updated_content["summary"] = ai_result.get("summary", "")
    updated_content["key_issues"] = ai_result.get("key_issues", [])
    # Enrich top_movers with AI reasons if available
    ai_movers = ai_result.get("top_movers", [])
    if ai_movers and updated_content.get("top_movers"):
        mover_reasons = {m.get("stock_name", ""): m.get("reason", "") for m in ai_movers}
        for mover in updated_content["top_movers"]:
            reason = mover_reasons.get(mover.get("stock_name", ""))
            if reason:
                mover["reason"] = reason

    briefing.content = updated_content
    db.commit()
    db.refresh(briefing)

    logger.info("Generated AI briefing for %s %s", market, target_date)
    return briefing


def _build_prompt(raw_data: dict) -> str:
    """Build the AI prompt from raw market data."""
    market = raw_data.get("market", "KR")
    market_name = "한국" if market == "KR" else "미국"
    date_str = raw_data.get("date", "")
    stats = raw_data.get("market_stats", {})
    top_movers = raw_data.get("top_movers", [])

    movers_text = ""
    for m in top_movers[:5]:
        name = m.get("stock_name", "")
        pct = m.get("change_pct", 0)
        vol = m.get("volume", 0)
        movers_text += f"- {name}: {pct:+.1f}% (거래량: {vol:,})\n"

    return f"""{date_str} {market_name} 시장 데이터를 기반으로 데일리 브리핑을 작성해주세요.

시장 현황:
- 상승 종목: {stats.get('stocks_up', 0)}개
- 하락 종목: {stats.get('stocks_down', 0)}개
- 보합: {stats.get('stocks_flat', 0)}개

특징주 (변동률 상위):
{movers_text}

다음 JSON 형식으로 응답해주세요:
{{"summary": "시장 전체 3줄 요약", "key_issues": [{{"title": "이슈 제목", "description": "설명"}}], "top_movers": [{{"stock_name": "종목명", "change_pct": 0.0, "reason": "변동 사유"}}]}}

규칙:
- summary는 3줄 이내로 시장 전반적 흐름을 설명
- key_issues는 3~5개
- top_movers는 상위 5개 종목의 변동 사유
- 모든 내용은 한국어로 작성"""


def _call_ai(raw_data: dict, max_retries: int = 3) -> dict | None:
    """Call Claude API to generate briefing content."""
    from app.config import get_settings

    settings = get_settings()
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY not set, skipping AI generation")
        return None

    prompt = _build_prompt(raw_data)

    for attempt in range(max_retries):
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )

            raw_text = message.content[0].text
            try:
                return json.loads(raw_text)
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI response (attempt %d)", attempt + 1)
                continue

        except Exception as e:
            logger.warning(
                "AI API call failed (attempt %d/%d): %s",
                attempt + 1,
                max_retries,
                e,
            )
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # exponential backoff
            continue

    return None


# Celery task — guarded behind try/except for environments without celery
try:
    from app.workers.celery_app import celery
    from app.config import get_settings
    from app.db.database import get_session_factory

    @celery.task(name="generate_market_briefing_task", bind=True, max_retries=0)
    def generate_market_briefing_task(self: object, market: str = "KR") -> dict:
        """Celery task: generate AI briefing from collected market data.

        Should be chained after collect_market_data_task.
        """
        settings = get_settings()
        factory = get_session_factory(settings.database_url)
        session = factory()
        try:
            briefing = generate_market_briefing(session, market=market)
            if briefing is None:
                return {"status": "error", "market": market}
            return {
                "status": "ok",
                "market": market,
                "date": str(briefing.date),
                "briefing_id": briefing.id,
            }
        finally:
            session.close()

except ImportError:
    generate_market_briefing_task = None  # type: ignore[assignment]
