"""中间件 - 监控 + 鉴权 + 错误处理 + Trace ID"""

import os
import time
import uuid

from fastapi import FastAPI, Request

from services.logging import logger
from services.auth import auth_service, AuthError
from services.metrics import metrics
from services.cache import _default_limiter
from services.error_handler import error_response

# 限流配置（可通过环境变量调整）
import os
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # 秒

# 无需鉴权的白名单路径
AUTH_WHITELIST = {
    "/health",
    "/ready",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
    "/api/v1/payment/webhook",
}


def is_whitelisted(path: str) -> bool:
    """检查路径是否在鉴权白名单中"""
    if path in AUTH_WHITELIST:
        return True
    # 静态资源和 docs 子路径
    if path.startswith("/docs/") or path.startswith("/openapi"):
        return True
    return False


def setup_middleware(app: FastAPI):
    """设置中间件"""

    @app.middleware("http")
    async def trace_middleware(request: Request, call_next):
        """注入请求级 trace ID，贯穿日志和响应头"""
        trace_id = request.headers.get("X-Trace-Id", uuid.uuid4().hex[:16])
        request.state.trace_id = trace_id

        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        """Clerk JWT 鉴权中间件"""
        path = request.url.path

        # 白名单路径跳过
        if is_whitelisted(path):
            return await call_next(request)

        # OPTIONS 预检请求跳过
        if request.method == "OPTIONS":
            return await call_next(request)

        # 未启用鉴权时跳过
        if not auth_service.enabled:
            # 开发模式：注入 mock 用户信息
            request.state.user_id = "dev_mock_user"
            return await call_next(request)

        # 获取 Token
        auth_header = request.headers.get("Authorization", "")
        api_key = request.headers.get("X-API-Key", "")

        # 优先验证 JWT
        if auth_header:
            try:
                payload = auth_service.verify_token(auth_header)
                request.state.user_id = payload.get("userId", "")
                request.state.user_payload = payload
                return await call_next(request)
            except AuthError as e:
                return error_response(status=e.status, message=e.message, code=e.code)

        # 其次验证 API Key（服务间调用）
        api_secret = os.getenv("API_SECRET", "")
        if api_secret and api_key == api_secret:
            request.state.user_id = "service"
            request.state.user_payload = {"sub": "service", "service": True}
            return await call_next(request)

        # 都没有则拒绝
        return error_response(status=401, message="未授权访问", code="unauthorized")

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        """全局限流中间件 - 按用户/IP维度限流"""
        path = request.url.path

        # 白名单路径跳过限流
        if is_whitelisted(path):
            return await call_next(request)

        # 限流 Key：优先用户 ID，其次 IP
        user_id = getattr(request.state, "user_id", None)
        client_ip = request.client.host if request.client else "unknown"
        rate_key = f"user:{user_id}" if user_id and user_id != "dev_mock_user" else f"ip:{client_ip}"

        allowed, remaining = await _default_limiter.is_allowed(
            rate_key, RATE_LIMIT_PER_MINUTE, RATE_LIMIT_WINDOW
        )

        if not allowed:
            metrics.inc("http_rate_limited_total")
            return error_response(
                status=429,
                message="请求过于频繁，请稍后再试",
                code="rate_limited",
                headers={
                    "X-RateLimit-Limit": str(RATE_LIMIT_PER_MINUTE),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # 添加限流响应头
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """记录所有 HTTP 请求"""
        start_time = time.time()
        trace_id = getattr(request.state, "trace_id", "-")

        # 记录请求
        logger.info(
            f"{request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
            trace_id=trace_id,
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # 统计指标
            metrics.inc("http_requests_total", labels={
                "method": request.method,
                "status": str(response.status_code),
            })
            metrics.observe("http_request_duration_seconds", duration, labels={
                "method": request.method,
            })

            # 记录响应
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code}",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=round(duration * 1000),
                trace_id=trace_id,
            )

            # 添加响应头
            response.headers["X-Process-Time"] = str(round(duration * 1000, 2))
            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"未处理异常: {str(e)}",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration * 1000),
                error=str(e),
                trace_id=trace_id,
            )
            return error_response(
                status=500,
                message="内部服务器错误",
                code="internal_error",
            )
