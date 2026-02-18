from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings


def create_celery_app() -> Celery:
    """Create and configure the Celery application."""
    settings = get_settings()
    app = Celery(
        "oh-my-stock",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Seoul",
        enable_utc=True,
        beat_schedule={
            "collect-krx-prices": {
                "task": "collect_krx_prices_task",
                "schedule": crontab(minute="*/30", hour="9-15", day_of_week="mon-fri"),
                "options": {"queue": "prices"},
            },
            "collect-us-prices": {
                "task": "collect_us_prices_task",
                "schedule": crontab(minute="*/30", hour="22-23,0-5", day_of_week="mon-fri"),
                "options": {"queue": "prices"},
            },
            "collect-dart-disclosures": {
                "task": "collect_dart_disclosures_task",
                "schedule": crontab(minute="0", hour="9-15", day_of_week="mon-fri"),
                "options": {"queue": "disclosures"},
            },
            "collect-stock-news": {
                "task": "collect_stock_news_task",
                "schedule": crontab(minute="15", hour="*/1"),
                "options": {"queue": "news"},
            },
            "run-e2e-pipeline": {
                "task": "run_e2e_pipeline_task",
                "schedule": crontab(minute="*/30", hour="9-15", day_of_week="mon-fri"),
                "options": {"queue": "pipeline"},
            },
        },
    )
    return app


celery = create_celery_app()
