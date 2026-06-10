"""中间件 - 监控 + 错误处理"""

import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from services.logging import logger


def setup_middleware(app: FastAPI):
    """设置中间件"""

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """记录所有 HTTP 请求"""
        start_time = time.time()

        # 记录请求
        logger.info(
            f"{request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # 记录响应
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code}",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=round(duration * 1000),
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
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "内部服务器错误"},
            )
