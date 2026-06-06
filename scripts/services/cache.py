"""Redis 缓存 + 限流服务"""

import hashlib
import json
import os
import time
from functools import wraps
from typing import Any

import redis.asyncio as aioredis


class CacheService:
    """Redis 缓存服务"""

    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client: aioredis.Redis | None = None
        self.default_ttl = 3600  # 1 hour

    async def connect(self):
        if not self.client:
            self.client = aioredis.from_url(self.url, decode_responses=True)
        return self.client

    async def close(self):
        if self.client:
            await self.client.close()
            self.client = None

    def _make_key(self, prefix: str, data: dict | str) -> str:
        """生成缓存键"""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        hash_val = hashlib.md5(data_str.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_val}"

    async def get(self, key: str) -> Any | None:
        """获取缓存"""
        client = await self.connect()
        value = await client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """设置缓存"""
        client = await self.connect()
        ttl = ttl or self.default_ttl
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        await client.setex(key, ttl, value)

    async def delete(self, key: str) -> None:
        """删除缓存"""
        client = await self.connect()
        await client.delete(key)

    async def cached(self, prefix: str, data: dict, ttl: int = 3600):
        """缓存装饰器 - 缓存函数结果"""
        key = self._make_key(prefix, data)
        cached = await self.get(key)
        if cached is not None:
            return cached
        return None  # 调用方需要实际执行并设置缓存


class RateLimiter:
    """限流器 - 滑动窗口算法"""

    def __init__(self):
        self.cache = CacheService()

    async def is_allowed(
        self, key: str, limit: int, window: int = 60
    ) -> tuple[bool, int]:
        """检查是否允许请求
        Args:
            key: 限流键（如 user_id）
            limit: 窗口期内最大请求数
            window: 时间窗口（秒）
        Returns:
            (是否允许, 剩余配额)
        """
        client = await self.cache.connect()
        now = time.time()
        window_start = now - window

        # 使用 sorted set 存储请求时间戳
        rate_key = f"rate:{key}"

        # 清理过期的记录
        await client.zremrangebyscore(rate_key, 0, window_start)

        # 获取当前窗口内的请求数
        count = await client.zcard(rate_key)

        if count >= limit:
            return False, 0

        # 记录新请求
        await client.zadd(rate_key, {f"{now}": now})
        await client.expire(rate_key, window)

        return True, limit - count - 1


def cache_result(prefix: str, ttl: int = 3600):
    """装饰器 - 缓存异步函数结果"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = CacheService()
            key = cache._make_key(
                f"{prefix}:{func.__name__}", {"args": str(args), "kwargs": str(kwargs)}
            )

            cached = await cache.get(key)
            if cached is not None:
                return cached

            result = await func(*args, **kwargs)
            if result is not None:
                await cache.set(key, result, ttl=ttl)
            return result

        return wrapper

    return decorator


def rate_limit(limit: int = 60, window: int = 60, key_func=None):
    """装饰器 - 限流"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            limiter = RateLimiter()
            key = key_func(*args, **kwargs) if key_func else "default"
            allowed, remaining = await limiter.is_allowed(key, limit, window)
            if not allowed:
                from fastapi import HTTPException

                raise HTTPException(status_code=429, detail="请求过于频繁")
            return await func(*args, **kwargs)

        return wrapper

    return decorator
