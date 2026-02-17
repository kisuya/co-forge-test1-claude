"""Tests for Redis caching layer (quality-005)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.core.cache import get_cached, invalidate_cache, invalidate_pattern, reset_redis_client


class TestGetCached:
    """Tests for the get_cached function."""

    def setup_method(self) -> None:
        reset_redis_client()

    def test_cache_miss_calls_fetch_fn(self) -> None:
        """On cache miss, fetch_fn should be called and result returned."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            result = get_cached("test:key", 300, lambda: {"data": "value"})

        assert result == {"data": "value"}
        mock_redis.setex.assert_called_once()

    def test_cache_hit_returns_cached_value(self) -> None:
        """On cache hit, cached value should be returned without calling fetch_fn."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = '{"data": "cached"}'
        fetch_fn = MagicMock(return_value={"data": "fresh"})

        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            result = get_cached("test:key", 300, fetch_fn)

        assert result == {"data": "cached"}
        fetch_fn.assert_not_called()

    def test_cache_miss_stores_result(self) -> None:
        """On cache miss, result should be stored in Redis with TTL."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            get_cached("test:key", 300, lambda: {"x": 1})

        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args
        assert args[0][0] == "test:key"
        assert args[0][1] == 300

    def test_redis_down_fallback_to_fetch(self) -> None:
        """When Redis is unavailable, fetch_fn should still be called."""
        with patch("app.core.cache.get_redis_client", return_value=None):
            result = get_cached("test:key", 300, lambda: {"fallback": True})

        assert result == {"fallback": True}

    def test_redis_get_error_fallback(self) -> None:
        """When Redis get raises an exception, fetch_fn should be called."""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("connection reset")

        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            result = get_cached("test:key", 300, lambda: {"error_fallback": True})

        assert result == {"error_fallback": True}

    def test_redis_set_error_still_returns_result(self) -> None:
        """When Redis set fails, result should still be returned."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.setex.side_effect = Exception("write error")

        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            result = get_cached("test:key", 300, lambda: {"data": "ok"})

        assert result == {"data": "ok"}


class TestInvalidateCache:
    """Tests for cache invalidation functions."""

    def setup_method(self) -> None:
        reset_redis_client()

    def test_invalidate_cache_deletes_key(self) -> None:
        """invalidate_cache should delete the specified key."""
        mock_redis = MagicMock()

        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            invalidate_cache("test:key")

        mock_redis.delete.assert_called_once_with("test:key")

    def test_invalidate_cache_redis_down(self) -> None:
        """invalidate_cache should not raise when Redis is down."""
        with patch("app.core.cache.get_redis_client", return_value=None):
            invalidate_cache("test:key")  # Should not raise

    def test_invalidate_pattern_deletes_matching_keys(self) -> None:
        """invalidate_pattern should delete all matching keys."""
        mock_redis = MagicMock()
        mock_redis.keys.return_value = ["user:1:search", "user:1:stocks"]

        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            invalidate_pattern("user:1:*")

        mock_redis.keys.assert_called_once_with("user:1:*")
        mock_redis.delete.assert_called_once_with("user:1:search", "user:1:stocks")

    def test_invalidate_pattern_no_matching_keys(self) -> None:
        """invalidate_pattern should not call delete when no keys match."""
        mock_redis = MagicMock()
        mock_redis.keys.return_value = []

        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            invalidate_pattern("nonexistent:*")

        mock_redis.delete.assert_not_called()

    def test_invalidate_pattern_redis_down(self) -> None:
        """invalidate_pattern should not raise when Redis is down."""
        with patch("app.core.cache.get_redis_client", return_value=None):
            invalidate_pattern("test:*")  # Should not raise
