from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

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
)
from services.error_handler import ServiceError
from services.logging import logger
from middleware import setup_middleware

app = FastAPI(
    title="智媒圈 API",
    description="AI自媒体内容工厂 - 后端服务",
    version="0.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_middleware(app)


@app.exception_handler(ServiceError)
async def service_error_handler(request, exc: ServiceError):
    logger.error("服务错误", code=exc.code, message=exc.message, path=request.url.path)
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=exc.status, content={"detail": exc.message, "code": exc.code}
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc: RequestValidationError):
    logger.warning("参数验证失败", errors=exc.errors(), path=request.url.path)
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=422, content={"detail": "参数验证失败", "errors": exc.errors()}
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
app.include_router(health.router, tags=["健康检查"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.5.0"}


@app.get("/metrics")
async def metrics():
    return {
        "requests_total": 0,
        "errors_total": 0,
        "active_users": 0,
        "cache_hit_rate": 0.0,
    }
