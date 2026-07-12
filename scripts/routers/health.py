"""健康检查端点"""

import os
from datetime import datetime
from fastapi import APIRouter
from services.logging import logger
from services.monitor import get_system_status, db_monitor, task_monitor, alert_manager

router = APIRouter()


@router.get("/health")
async def health():
    """Liveness probe"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "0.7.0",
    }


@router.get("/ready")
async def ready():
    """Readiness probe - 检查依赖"""
    checks = {
        "api": "ok",
        "redis": "unavailable",
        "deepseek": "unavailable",
    }

    try:
        import redis

        r = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"), socket_timeout=2
        )
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        logger.warning("Redis 不可用", error=str(e))
        checks["redis"] = "degraded"

    if os.getenv("DEEPSEEK_API_KEY"):
        checks["deepseek"] = "ok"

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "ready" if all_ok else "degraded",
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/status")
async def status():
    """获取完整系统状态"""
    alert_manager.check_health(db_monitor, task_monitor)
    return get_system_status()


@router.get("/alerts")
async def alerts(status: str = "active"):
    """获取告警列表"""
    return {
        "alerts": alert_manager.get_alerts(status),
        "timestamp": datetime.now().isoformat(),
    }
