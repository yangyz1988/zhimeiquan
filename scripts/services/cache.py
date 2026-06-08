"""Redis 缓存 + 限流服务（Redis 不可用时自动降级为内存缓存）"""

import hashlib
import json
import os
import time
from functools import wraps
from typing import Any

import redis.asyncio as aioredis
from services.logging import logger


class CacheService:
    """Redis 缓存服务（Redis 不可用时自动降级为内存缓存）"""

    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client: aioredis.Redis | None = None
        self.default_ttl = 3600
        self._memory_cache: dict[str, tuple[float, Any]] = {}
        self._redis_checked = False
        self._redis_ok = False

    async def connect(self) -> aioredis.Redis:
        if not self.client:
            self.client = aioredis.from_url(self.url, decode_responses=True)
        return self.client

    async def close(self):
        if self.client:
            await self.client.close()
            self.client = None
        self._redis_checked = False
        self._redis_ok = False

    async def _try_redis(self) -> bool:
        if self._redis_checked:
            return self._redis_ok
        try:
            client = await self.connect()
            await client.ping()
            self._redis_ok = True
        except Exception:
            self._redis_ok = False
            logger.warning("Redis 不可用，降级为内存缓存", url=self.url)
        self._redis_checked = True
        return self._redis_ok

    def _mem_get(self, key: str) -> Any | None:
        if key in self._memory_cache:
            expires, value = self._memory_cache[key]
            if time.time() < expires:
                return value
            del self._memory_cache[key]
        return None

    def _mem_set(self, key: str, value: Any, ttl: int | None = None):
        ttl = ttl or self.default_ttl
        self._memory_cache[key] = (time.time() + ttl, value)
        if len(self._memory_cache) > 1000:
            oldest = sorted(self._memory_cache.items(), key=lambda x: x[1][0])[:100]
            for k, _ in oldest:
                del self._memory_cache[k]

    def _make_key(self, prefix: str, data: dict | str) -> str:
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        hash_val = hashlib.md5(data_str.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_val}"

    async def get(self, key: str) -> Any | None:
        if await self._try_redis():
            try:
                value = await (await self.connect()).get(key)
                if value:
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
            except Exception:
                self._redis_ok = False
        return self._mem_get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None):
        ttl = ttl or self.default_ttl
        serialized = (
            json.dumps(value, ensure_ascii=False)
            if isinstance(value, (dict, list))
            else str(value)
        )
        if await self._try_redis():
            try:
                await (await self.connect()).setex(key, ttl, serialized)
            except Exception:
                self._redis_ok = False
        self._mem_set(key, value, ttl)

    async def delete(self, key: str):
        if await self._try_redis():
            try:
                await (await self.connect()).delete(key)
            except Exception:
                self._redis_ok = False
        self._memory_cache.pop(key, None)

    async def cached(self, prefix: str, data: dict, ttl: int = 3600):
        key = self._make_key(prefix, data)
        cached = await self.get(key)
        if cached is not None:
            return cached
        return None


class RateLimiter:
    """限流器 - 滑动窗口算法（Redis 不可用时自动降级为内存限流）"""

    def __init__(self):
        self.cache = CacheService()
        self._memory_requests: dict[str, list[float]] = {}

    async def is_allowed(
        self, key: str, limit: int, window: int = 60
    ) -> tuple[bool, int]:
        if await self.cache._try_redis():
            try:
                return await self._redis_check(key, limit, window)
            except Exception:
                self.cache._redis_ok = False

        return self._memory_check(key, limit, window)

    async def _redis_check(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        client = await self.cache.connect()
        now = time.time()
        rate_key = f"rate:{key}"
        await client.zremrangebyscore(rate_key, 0, now - window)
        count = await client.zcard(rate_key)
        if count >= limit:
            return False, 0
        await client.zadd(rate_key, {f"{now}": now})
        await client.expire(rate_key, window)
        return True, limit - count - 1

    def _memory_check(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        now = time.time()
        if key not in self._memory_requests:
            self._memory_requests[key] = []
        self._memory_requests[key] = [
            t for t in self._memory_requests[key] if t > now - window
        ]
        count = len(self._memory_requests[key])
        if count >= limit:
            return False, 0
        self._memory_requests[key].append(now)
        return True, limit - count - 1


def cache_result(prefix: str, ttl: int = 3600):
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
