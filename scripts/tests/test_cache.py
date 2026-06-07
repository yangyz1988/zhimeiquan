"""缓存 + 限流测试"""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from services.cache import CacheService, RateLimiter, cache_result, rate_limit


@pytest.mark.asyncio
async def test_cache_make_key():
    cache = CacheService()
    key1 = cache._make_key("test", {"a": 1, "b": 2})
    key2 = cache._make_key("test", {"b": 2, "a": 1})  # 顺序不同但结果相同
    assert key1 == key2
    assert key1.startswith("test:")


@pytest.mark.asyncio
async def test_cache_get_set():
    """使用模拟 Redis 测试缓存"""
    with patch.object(CacheService, "connect") as mock_connect:
        mock_redis = AsyncMock()
        mock_redis.get.return_value = '{"value": "test"}'
        mock_redis.setex = AsyncMock()
        mock_connect.return_value = mock_redis

        cache = CacheService()
        result = await cache.get("test_key")
        assert result == {"value": "test"}

        await cache.set("test_key", {"data": 1}, ttl=60)
        mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limiter_allowed():
    with patch.object(CacheService, "connect") as mock_connect:
        mock_redis = AsyncMock()
        mock_redis.zremrangebyscore = AsyncMock()
        mock_redis.zcard.return_value = 0
        mock_redis.zadd = AsyncMock()
        mock_redis.expire = AsyncMock()
        mock_connect.return_value = mock_redis

        limiter = RateLimiter()
        allowed, remaining = await limiter.is_allowed("user_1", limit=5, window=60)
        assert allowed is True
        assert remaining == 4


@pytest.mark.asyncio
async def test_rate_limiter_denied():
    with patch.object(CacheService, "connect") as mock_connect:
        mock_redis = AsyncMock()
        mock_redis.zremrangebyscore = AsyncMock()
        mock_redis.zcard.return_value = 5  # 已达上限
        mock_connect.return_value = mock_redis

        limiter = RateLimiter()
        allowed, remaining = await limiter.is_allowed("user_1", limit=5, window=60)
        assert allowed is False
        assert remaining == 0
