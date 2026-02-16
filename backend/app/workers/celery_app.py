from __future__ import annotations

from celery import Celery

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
    )
    return app


celery = create_celery_app()
