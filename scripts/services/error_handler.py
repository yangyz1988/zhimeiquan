"""错误处理 + 重试 + 熔断"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable

from services.logging import logger


class ServiceError(Exception):
    """业务错误基类"""

    def __init__(self, message: str, code: str = "service_error", status: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


class RateLimitError(ServiceError):
    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(message, code="rate_limit", status=429)


class ValidationError(ServiceError):
    def __init__(self, message: str):
        super().__init__(message, code="validation_error", status=400)


class APIKeyError(ServiceError):
    def __init__(self, message: str = "API Key 未配置"):
        super().__init__(message, code="api_key_missing", status=500)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """重试装饰器 - 指数退避"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} 重试 {max_attempts} 次后失败",
                            function=func.__name__,
                            error=str(e),
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} 第 {attempt} 次失败，{current_delay}s 后重试",
                        function=func.__name__,
                        attempt=attempt,
                        error=str(e),
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

            raise last_error

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt == max_attempts:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff

            raise last_error

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class CircuitBreaker:
    """熔断器"""

    def __init__(self, failure_threshold: int = 5, recovery_time: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed / open / half_open

    async def acall(self, func: Callable, *args, **kwargs) -> Any:
        """执行受保护的异步方法"""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_time:
                self.state = "half_open"
            else:
                raise ServiceError("服务暂时不可用", code="circuit_open", status=503)

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """执行受保护的方法"""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_time:
                self.state = "half_open"
            else:
                raise ServiceError("服务暂时不可用", code="circuit_open", status=503)

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning("熔断器开启", failure_count=self.failure_count)


# 全局熔断器
ai_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_time=60)
