import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from routers import (
    content,
    titles,
    score,
    rules,
    ab_test,
    analytics,
    video,
    calendar,
    image,
    templates,
    agent,
    team,
    model_router,
    health,
    insights,
    fire_score,
    competitors,
    stream,
    insights_reports,
    calibrate,
    knowledge,
    payment,
    media_assets,
    comments,
    tags,
    subscriptions,
    channels,
    publish_logs,
    trends,
)
from services.error_handler import ServiceError, error_response
from services.logging import logger
from services.env_validator import print_validation
from services.metrics import metrics
from monitors.browser import get_browser_pool, _browser_pool
from middleware import setup_middleware

app = FastAPI(
    title="智媒圈 API",
    description="AI内容策略引擎 - 后端服务",
    version="0.7.0",
)

# BrowserPool lifespan 集成 - 启动时初始化浏览器池，关闭时优雅清理
@app.on_event("startup")
async def startup_browser_pool():
    """应用启动时预热 BrowserPool（如果浏览器采集已启用）"""
    try:
        from monitors.browser import is_browser_enabled
        if is_browser_enabled():
            logger.info("启动 BrowserPool...")
            await get_browser_pool()
            logger.info("BrowserPool 已就绪")
        else:
            logger.info("浏览器采集已禁用，跳过 BrowserPool 初始化")
    except Exception as e:
        logger.warning(f"BrowserPool 启动失败（非致命）: {e}")


@app.on_event("shutdown")
async def shutdown_browser_pool():
    """应用关闭时清理 BrowserPool 和残留 Chromium 进程"""
    global _browser_pool
    if _browser_pool is not None:
        try:
            await _browser_pool.stop()
            _browser_pool = None
            logger.info("BrowserPool 已优雅关闭")
        except Exception as e:
            logger.error(f"BrowserPool 关闭异常: {e}")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    os.getenv("FRONTEND_URL", "https://www.zhimeiquan.com"),
]

# 生产环境收紧 CORS，只允许正式域名
ENV = os.getenv("ENV", "development")
if ENV == "production":
    ALLOWED_ORIGINS = [os.getenv("FRONTEND_URL", "https://www.zhimeiquan.com")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    max_age=86400,
)

setup_middleware(app)

# 启动时环境变量校验
logger.info("执行环境变量校验...")
env_valid = print_validation()
if not env_valid:
    logger.warning("环境变量校验未完全通过，部分功能可能不可用")


@app.exception_handler(ServiceError)
async def service_error_handler(request, exc: ServiceError):
    logger.error("服务错误", code=exc.code, message=exc.message, path=request.url.path)
    return error_response(status=exc.status, message=exc.message, code=exc.code)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc: RequestValidationError):
    logger.warning("参数验证失败", errors=exc.errors(), path=request.url.path)
    return error_response(
        status=422,
        message="参数验证失败",
        code="validation_error",
        detail={"errors": exc.errors()},
    )


app.include_router(content.router, prefix="/api/v1/content", tags=["内容生成"])
app.include_router(titles.router, prefix="/api/v1/titles", tags=["标题生成"])
app.include_router(score.router, prefix="/api/v1/content", tags=["内容评分"])
app.include_router(rules.router, prefix="/api/v1/monitor", tags=["爆款监控"])
app.include_router(video.router, prefix="/api/v1/video", tags=["视频生成"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["数据闭环"])
app.include_router(ab_test.router, prefix="/api/v1/ab-test", tags=["A/B测试"])
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["内容调度"])
app.include_router(image.router, prefix="/api/v1/image", tags=["图像生成"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["模板系统"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["自主Agent"])
app.include_router(team.router, prefix="/api/v1/team", tags=["团队协作"])
app.include_router(model_router.router, prefix="/api/v1/router", tags=["模型路由"])
app.include_router(insights.router, prefix="/api/v1/insights", tags=["内容洞察"])
app.include_router(fire_score.router, prefix="/api/v1/fire-score", tags=["Fire Score 校准"])
app.include_router(competitors.router, prefix="/api/v1/competitors", tags=["竞品监控"])
app.include_router(stream.router, prefix="/api/v1/stream", tags=["流式生成"])
app.include_router(insights_reports.router, prefix="/api/insights", tags=["分析报告"])
app.include_router(calibrate.router, prefix="/api/v1/calibrate", tags=["Fire Score 校准"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["知识图谱"])
app.include_router(payment.router, prefix="/api/v1/payment", tags=["支付"])
app.include_router(health.router, tags=["健康检查"])
app.include_router(media_assets.router, prefix="/api/v1/media", tags=["媒体资产"])
app.include_router(comments.router, prefix="/api/v1/comments", tags=["协作评论"])
app.include_router(tags.router, prefix="/api/v1/tags", tags=["标签体系"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["订阅管理"])
app.include_router(channels.router, prefix="/api/v1/channels", tags=["分发渠道"])
app.include_router(publish_logs.router, prefix="/api/v1/publish-logs", tags=["发布日志"])
app.include_router(trends.router, prefix="/api/v1/trends", tags=["热点追踪"])


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "0.7.0",
        "service": "zhimeiquan-api",
    }


@app.get("/ready")
async def ready():
    """就绪检查 - 包含依赖状态"""
    checks: dict[str, str | dict] = {"api": "ok"}

    # 数据库连通性检查
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url:
        try:
            if "postgresql" in db_url or "postgres" in db_url:
                import asyncpg
                conn = await asyncpg.connect(db_url, timeout=5)
                await conn.execute("SELECT 1")
                await conn.close()
            elif "sqlite" in db_url:
                import sqlite3
                db_path = db_url.replace("sqlite:", "").replace("file:", "").lstrip("/")
                conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
                conn.execute("SELECT 1")
                conn.close()
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {type(e).__name__}"
    else:
        checks["database"] = "not_configured"

    # Redis 连通性检查（可选依赖）
    redis_url = os.environ.get("REDIS_URL", "")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url, socket_connect_timeout=3)
            r.ping()
            r.close()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "unavailable (degraded)"

    # LLM API 连通性检查（轻量）
    if "DEEPSEEK_API_KEY" in os.environ:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    "https://api.deepseek.com/v1/models",
                    headers={"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}"},
                )
                checks["llm"] = "ok" if resp.status_code == 200 else f"status_{resp.status_code}"
        except Exception as e:
            checks["llm"] = f"error: {type(e).__name__}"

    all_ok = all(
        v == "ok" for v in checks.values()
        if isinstance(v, str) and v != "unavailable (degraded)"
    )

    return {
        "status": "ready" if all_ok else "degraded",
        "version": "0.7.0",
        "checks": checks,
    }


@app.get("/metrics")
async def get_metrics():
    """Prometheus 风格指标端点"""
    # 统计活跃用户（简化版）
    data = metrics.export()

    return {
        "uptime_seconds": data["uptime_seconds"],
        "requests_total": data["counters"].get("http_requests_total", 0),
        "errors_total": data["counters"].get("http_requests_total{status=\"error\"}", 0),
        "active_users": data["gauges"].get("active_users", 0),
        "cache_hit_rate": data["gauges"].get("cache_hit_rate", 0.0),
        "avg_response_time_ms": round(
            data["histograms"].get("http_request_duration_seconds", {}).get("avg", 0) * 1000, 2
        ),
        "detail": data,
    }
