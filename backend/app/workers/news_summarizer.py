"""AI news summarization and importance classification (news-002).

Processes unsummarized NewsArticle entries in batches, calling Claude API
to generate 1-line summaries and classify importance.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.news_article import NewsArticle

logger = logging.getLogger(__name__)

MAX_TOKENS_PER_ARTICLE = 100
BATCH_SIZE = 20


def summarize_news(
    db: Session,
    *,
    batch_size: int = BATCH_SIZE,
    summarize_fn: object | None = None,
    max_retries: int = 3,
) -> list[NewsArticle]:
    """Summarize unsummarized news articles and classify importance.

    Args:
        db: Database session.
        batch_size: Maximum articles to process per call.
        summarize_fn: Override for AI summarization (for testing).
            Should accept (title: str) and return {"summary": str, "importance": str}.
        max_retries: Retry count for AI API calls.

    Returns:
        List of updated NewsArticle entries.
    """
    # Fetch unsummarized articles (content_summary is NULL)
    articles = list(
        db.execute(
            select(NewsArticle)
            .where(NewsArticle.content_summary.is_(None))
            .order_by(NewsArticle.created_at.desc())
            .limit(batch_size)
        ).scalars().all()
    )

    if not articles:
        logger.info("No unsummarized articles found")
        return []

    updated: list[NewsArticle] = []

    for article in articles:
        if summarize_fn is not None:
            result = summarize_fn(article.title)
        else:
            result = _call_ai_summarize(article.title, max_retries=max_retries)

        if result is None:
            # Fallback: use title as summary
            article.content_summary = article.title[:50]
            article.importance = "low"
        else:
            article.content_summary = result.get("summary", article.title[:50])
            importance = result.get("importance", "low")
            if importance not in ("high", "medium", "low"):
                importance = "low"
            article.importance = importance

            # Parse sentiment (added with analysis-008)
            sentiment = result.get("sentiment", "neutral")
            if sentiment not in ("positive", "negative", "neutral"):
                sentiment = "neutral"
            article.sentiment = sentiment

            score = result.get("sentiment_score")
            if score is not None:
                try:
                    score = float(score)
                    score = max(-1.0, min(1.0, score))
                except (TypeError, ValueError):
                    score = 0.0
            else:
                # Derive score from sentiment label
                score = {"positive": 0.5, "negative": -0.5, "neutral": 0.0}.get(sentiment, 0.0)
            article.sentiment_score = score

        updated.append(article)

    db.commit()
    logger.info("Summarized %d news articles", len(updated))
    return updated


def _build_summarize_prompt(title: str) -> str:
    """Build prompt for single article summarization."""
    return f"""다음 뉴스 제목을 분석하여 요약, 중요도, 감성을 분류해주세요.

뉴스 제목: {title}

다음 JSON 형식으로 응답해주세요:
{{"summary": "50자 이내 1줄 요약", "importance": "high|medium|low", "sentiment": "positive|negative|neutral", "sentiment_score": 0.0}}

중요도 기준:
- high: 주가에 직접 영향 (실적발표, 대규모 계약, 규제 변경)
- medium: 간접 영향 (업계 동향, 경쟁사 소식)
- low: 낮은 관련성

감성 기준:
- positive: 주가에 긍정적 영향 (호재)
- negative: 주가에 부정적 영향 (악재)
- neutral: 중립적
- sentiment_score: -1.0(매우 부정) ~ 1.0(매우 긍정) 실수

규칙:
- summary는 50자 이내
- importance는 반드시 high, medium, low 중 하나
- sentiment는 반드시 positive, negative, neutral 중 하나
- 한국어로 작성"""


def _call_ai_summarize(title: str, max_retries: int = 3) -> dict | None:
    """Call Claude API to summarize a news article."""
    from app.config import get_settings

    settings = get_settings()
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY not set, skipping AI summarization")
        return None

    prompt = _build_summarize_prompt(title)

    for attempt in range(max_retries):
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=MAX_TOKENS_PER_ARTICLE,
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
                time.sleep(2 ** attempt)
            continue

    return None


# Celery task — guarded behind try/except for environments without celery
try:
    from app.workers.celery_app import celery
    from app.config import get_settings
    from app.db.database import get_session_factory

    @celery.task(name="summarize_news_task", bind=True, max_retries=0)
    def summarize_news_task(self) -> dict:
        """Celery task: summarize unsummarized news articles."""
        settings = get_settings()
        factory = get_session_factory(settings.database_url)
        session = factory()
        try:
            articles = summarize_news(session)
            return {"status": "ok", "articles_summarized": len(articles)}
        except Exception as exc:
            logger.exception("summarize_news_task failed: %s", exc)
            return {"status": "error", "error": str(exc)}
        finally:
            session.close()

except ImportError:
    summarize_news_task = None  # type: ignore[assignment]
