"""健康检查端点"""

from datetime import datetime
from fastapi import APIRouter
from services.logging import logger

router = APIRouter()


@router.get("/health")
async def health():
    """Liveness probe"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "0.5.0",
    }


@router.get("/ready")
async def ready():
    """Readiness probe - 检查依赖"""
    checks = {
        "api": True,
        "redis": False,
        "deepseek": False,
    }

    try:
        import redis
        import os

        r = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"), socket_timeout=2
        )
        r.ping()
        checks["redis"] = True
    except Exception as e:
        logger.warning("Redis 不可用", error=str(e))

    if os.getenv("DEEPSEEK_API_KEY"):
        checks["deepseek"] = True

    return {
        "status": "ready" if checks["api"] else "not_ready",
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
    }
