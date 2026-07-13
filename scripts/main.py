"""FastAPI 路由模块

提供完整的 RESTful API 端点，包含 OpenAPI 文档。
"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
import time
import logging
from typing import Optional

from routers import (
    media_assets,
    comments,
    tags,
    subscriptions,
    channels,
    publish_logs,
    trends,
)
from services.database import Database
from services.performance import PerformanceMonitor

# ─────────────────────────────────────────
# 应用初始化
# ─────────────────────────────────────────

logger = logging.getLogger(__name__)

app = FastAPI(
    title="智媒圈 API",
    description="""
## 智媒圈 — 智能内容运营平台

提供全方位的内容管理、协作评论、热点追踪、订阅管理和分发渠道功能。

### 主要功能
- **媒体资产管理**: 上传、存储、管理图片/视频等媒体资源
- **协作评论**: 多人协作评论和审核流程
- **标签体系**: 内容标签分类和智能推荐
- **订阅管理**: 用户订阅和计费周期管理
- **分发渠道**: 多平台内容分发
- **热点追踪**: 实时热点监测和推荐

### 认证方式
使用 Bearer Token 认证，在请求头添加：
```
Authorization: Bearer <your_token>
```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "media", "description": "媒体资源管理"},
        {"name": "comments", "description": "评论管理"},
        {"name": "tags", "description": "标签管理"},
        {"name": "subscriptions", "description": "订阅管理"},
        {"name": "channels", "description": "分发渠道"},
        {"name": "trends", "description": "热点追踪"},
        {"name": "logs", "description": "发布日志"},
        {"name": "health", "description": "健康检查"},
    ],
    contact={
        "name": "智媒圈技术支持",
        "email": "support@zhimeiquan.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# ─────────────────────────────────────────
# CORS 配置
# ─────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://zhimeiquan.com",
        "https://*.zhimeiquan.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────
# 中间件
# ─────────────────────────────────────────

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加处理时间头"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.3f}s"
    
    # 记录慢请求
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.3f}s")
    
    return response


@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    """全局异常捕获"""
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)},
        )


# ─────────────────────────────────────────
# 依赖注入
# ─────────────────────────────────────────

async def get_current_user(request: Request) -> dict:
    """获取当前用户（认证中间件）"""
    # 从请求头获取 token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未认证")
    
    token = auth_header[7:]
    # TODO: 验证 JWT token
    # 这里简化处理，实际应验证 token 并返回用户信息
    return {"user_id": "test-user", "role": "admin"}


async def get_db() -> Database:
    """获取数据库实例"""
    return Database()


# ─────────────────────────────────────────
# 健康检查
# ─────────────────────────────────────────

@app.get("/health", tags=["health"])
async def health_check():
    """
    健康检查端点
    
    返回服务状态和各组件健康度。
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "database": "ok",
            "redis": "ok",
            "storage": "ok",
        },
        "timestamp": time.time(),
    }


@app.get("/health/ready", tags=["health"])
async def readiness_check():
    """
    就绪检查端点
    
    用于 Kubernetes 就绪探针。
    """
    # 检查数据库连接
    try:
        db = Database()
        db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {e}")


@app.get("/health/live", tags=["health"])
async def liveness_check():
    """
    存活检查端点
    
    用于 Kubernetes 存活探针。
    """
    return {"status": "alive"}


# ─────────────────────────────────────────
# 注册路由
# ─────────────────────────────────────────

app.include_router(
    media_assets.router,
    prefix="/api/v1/media",
    tags=["media"],
)
app.include_router(
    comments.router,
    prefix="/api/v1/comments",
    tags=["comments"],
)
app.include_router(
    tags.router,
    prefix="/api/v1/tags",
    tags=["tags"],
)
app.include_router(
    subscriptions.router,
    prefix="/api/v1/subscriptions",
    tags=["subscriptions"],
)
app.include_router(
    channels.router,
    prefix="/api/v1/channels",
    tags=["channels"],
)
app.include_router(
    publish_logs.router,
    prefix="/api/v1/logs",
    tags=["logs"],
)
app.include_router(
    trends.router,
    prefix="/api/v1/trends",
    tags=["trends"],
)


# ─────────────────────────────────────────
# 根端点
# ─────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    """API 根端点"""
    return {
        "name": "智媒圈 API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }


# ─────────────────────────────────────────
# 启动/关闭事件
# ─────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("智媒圈 API 启动")
    # 初始化数据库连接池
    # 初始化 Redis 连接
    # 初始化其他资源


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("智媒圈 API 关闭")
    # 关闭数据库连接池
    # 关闭 Redis 连接
    # 清理其他资源


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )