"""Redis 缓存服务

功能:
- 缓存管理
- 限流
- 分布式锁
- 消息队列
"""

import os
import json
import hashlib
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List, Callable, Awaitable
from functools import wraps
import redis.asyncio as aioredis
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ========================================
# 配置
# ========================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# 限流配置
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# 缓存前缀
CACHE_PREFIX = "zhimeiquan:"
CACHE_DEFAULT_TTL = 300  # 5分钟

# ========================================
# 模型
# ========================================

class RateLimitResult(BaseModel):
    allowed: bool
    remaining: int
    reset_at: int
    retry_after: Optional[int] = None


class LockResult(BaseModel):
    acquired: bool
    token: Optional[str] = None
    ttl: Optional[int] = None


# ========================================
# Redis 客户端
# ========================================

class RedisClient:
    """Redis 客户端"""

    _instance: Optional['RedisClient'] = None
    _pool: Optional[aioredis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        """建立连接"""
        if self._pool is None:
            self._pool = aioredis.from_url(
                REDIS_URL,
                password=REDIS_PASSWORD or None,
                db=REDIS_DB,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
            )
        return self._pool

    async def disconnect(self):
        """关闭连接"""
        if self._pool:
            await self._pool.close()
            self._pool = None

    @property
    def client(self) -> aioredis.Redis:
        """获取客户端"""
        if self._pool is None:
            raise RuntimeError("Redis 未连接，请先调用 connect()")
        return self._pool


# ========================================
# 缓存服务
# ========================================

class CacheService:
    """缓存服务"""

    def __init__(self, client: RedisClient):
        self.client = client

    def _key(self, key: str) -> str:
        """生成完整键"""
        return f"{CACHE_PREFIX}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        full_key = self._key(key)
        value = await self.client.client.get(full_key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = CACHE_DEFAULT_TTL
    ) -> bool:
        """设置缓存"""
        full_key = self._key(key)
        serialized = json.dumps(value) if not isinstance(value, str) else value
        return await self.client.client.setex(full_key, ttl, serialized)

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        full_key = self._key(key)
        return await self.client.client.delete(full_key) > 0

    async def exists(self, key: str) -> bool:
        """检查存在"""
        full_key = self._key(key)
        return await self.client.client.exists(full_key) > 0

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]],
        ttl: int = CACHE_DEFAULT_TTL
    ) -> Any:
        """获取或设置缓存"""
        value = await self.get(key)
        if value is not None:
            return value

        value = await factory()
        await self.set(key, value, ttl)
        return value

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取"""
        full_keys = [self._key(k) for k in keys]
        values = await self.client.client.mget(full_keys)
        result = {}
        for key, value in zip(keys, values):
            if value is not None:
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value
        return result

    async def mset(self, mapping: Dict[str, Any], ttl: int = CACHE_DEFAULT_TTL) -> bool:
        """批量设置"""
        pipe = self.client.client.pipeline()
        for key, value in mapping.items():
            full_key = self._key(key)
            serialized = json.dumps(value) if not isinstance(value, str) else value
            pipe.setex(full_key, ttl, serialized)
        await pipe.execute()
        return True

    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配键"""
        full_pattern = self._key(pattern)
        keys = await self.client.client.keys(full_pattern)
        if keys:
            return await self.client.client.delete(*keys)
        return 0


# ========================================
# 限流服务
# ========================================

class RateLimiter:
    """限流器"""

    def __init__(self, client: RedisClient):
        self.client = client

    def _key(self, identifier: str, action: str = "default") -> str:
        """生成限流键"""
        return f"{CACHE_PREFIX}ratelimit:{action}:{identifier}"

    async def check(
        self,
        identifier: str,
        action: str = "default",
        max_requests: int = RATE_LIMIT_PER_MINUTE,
        window: int = RATE_LIMIT_WINDOW
    ) -> RateLimitResult:
        """检查限流"""
        key = self._key(identifier, action)
        now = int(datetime.utcnow().timestamp())
        window_start = now - window

        # 使用滑动窗口算法
        pipe = self.client.client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window)
        results = await pipe.execute()

        current_count = results[1]
        remaining = max(0, max_requests - current_count - 1)

        allowed = current_count < max_requests
        result = RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_at=now + window,
        )

        if not allowed:
            result.retry_after = window

        return result

    async def reset(self, identifier: str, action: str = "default") -> bool:
        """重置限流"""
        key = self._key(identifier, action)
        return await self.client.client.delete(key) > 0


# ========================================
# 分布式锁
# ========================================

class DistributedLock:
    """分布式锁"""

    def __init__(self, client: RedisClient):
        self.client = client

    def _key(self, resource: str) -> str:
        """生成锁键"""
        return f"{CACHE_PREFIX}lock:{resource}"

    async def acquire(
        self,
        resource: str,
        ttl: int = 10,
        timeout: int = 5
    ) -> LockResult:
        """获取锁"""
        key = self._key(resource)
        token = hashlib.sha256(f"{resource}:{datetime.utcnow().isoformat()}".encode()).hexdigest()

        start = asyncio.get_event_loop().time()
        while True:
            acquired = await self.client.client.set(key, token, nx=True, ex=ttl)
            if acquired:
                return LockResult(acquired=True, token=token, ttl=ttl)

            elapsed = asyncio.get_event_loop().time() - start
            if elapsed >= timeout:
                return LockResult(acquired=False)

            await asyncio.sleep(0.1)

    async def release(self, resource: str, token: str) -> bool:
        """释放锁"""
        key = self._key(resource)
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        return await self.client.client.eval(script, 1, key, token) > 0

    async def extend(self, resource: str, token: str, ttl: int = 10) -> bool:
        """延长锁"""
        key = self._key(resource)
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """
        return await self.client.client.eval(script, 1, key, token, ttl) > 0


# ========================================
# 装饰器
# ========================================

def cached(
    key: str,
    ttl: int = CACHE_DEFAULT_TTL,
    key_builder: Optional[Callable] = None
):
    """缓存装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 构建键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = key

            # 获取缓存
            cache = CacheService(redis_client)
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 设置缓存
            await cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


def rate_limit(
    action: str = "default",
    max_requests: int = RATE_LIMIT_PER_MINUTE,
    window: int = RATE_LIMIT_WINDOW,
    identifier_func: Optional[Callable] = None
):
    """限流装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取标识符
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                # 默认使用第一个参数（通常是 request）
                request = args[0] if args else None
                identifier = getattr(request, "client", {}).get("host", "unknown")

            # 检查限流
            limiter = RateLimiter(redis_client)
            result = await limiter.check(identifier, action, max_requests, window)

            if not result.allowed:
                raise Exception(f"请求过于频繁，请 {result.retry_after} 秒后重试")

            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ========================================
# 全局实例
# ========================================

redis_client = RedisClient()
cache_service = CacheService(redis_client)
rate_limiter = RateLimiter(redis_client)
distributed_lock = DistributedLock(redis_client)