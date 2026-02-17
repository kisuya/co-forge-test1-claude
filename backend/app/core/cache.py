"""Redis caching layer with graceful degradation."""
from __future__ import annotations

import json
import logging
from typing import Any, Callable, TypeVar

import redis

from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis | None:
    """Get a Redis client instance. Returns None if connection fails."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        settings = get_settings()
        client = redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        _redis_client = client
        return client
    except Exception:
        logger.warning("Redis connection failed, caching disabled")
        return None


def reset_redis_client() -> None:
    """Reset the cached Redis client (for testing)."""
    global _redis_client
    _redis_client = None


def get_cached(key: str, ttl: int, fetch_fn: Callable[[], T]) -> T:
    """Get value from cache or fetch and store it.

    Args:
        key: Cache key.
        ttl: Time-to-live in seconds.
        fetch_fn: Function to call on cache miss.

    Returns:
        Cached or freshly fetched value.
    """
    client = get_redis_client()
    if client is not None:
        try:
            cached = client.get(key)
            if cached is not None:
                return json.loads(cached)
        except Exception:
            logger.warning("Redis get failed for key %s", key)

    result = fetch_fn()

    if client is not None:
        try:
            client.setex(key, ttl, json.dumps(result, default=str))
        except Exception:
            logger.warning("Redis set failed for key %s", key)

    return result


def invalidate_cache(key: str) -> None:
    """Delete a cache key."""
    client = get_redis_client()
    if client is not None:
        try:
            client.delete(key)
        except Exception:
            logger.warning("Redis delete failed for key %s", key)


def invalidate_pattern(pattern: str) -> None:
    """Delete all keys matching a pattern."""
    client = get_redis_client()
    if client is not None:
        try:
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
        except Exception:
            logger.warning("Redis pattern delete failed for %s", pattern)
