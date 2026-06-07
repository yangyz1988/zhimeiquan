"""错误处理 + 重试测试"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from services.error_handler import (
    ServiceError,
    RateLimitError,
    ValidationError,
    APIKeyError,
    retry,
    CircuitBreaker,
    ai_circuit_breaker,
)


def test_service_error():
    err = ServiceError("test", code="test_code", status=400)
    assert err.message == "test"
    assert err.code == "test_code"
    assert err.status == 400


def test_rate_limit_error():
    err = RateLimitError()
    assert err.status == 429
    assert err.code == "rate_limit"


def test_validation_error():
    err = ValidationError("invalid input")
    assert err.status == 400
    assert err.code == "validation_error"


def test_api_key_error():
    err = APIKeyError()
    assert "API Key" in err.message
    assert err.status == 500


@pytest.mark.asyncio
async def test_retry_success():
    """重试装饰器 - 第一次成功"""
    call_count = 0

    @retry(max_attempts=3, delay=0.01)
    async def func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await func()
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_eventual_success():
    """重试装饰器 - 最终成功"""
    call_count = 0

    @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
    async def func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("temp error")
        return "success"

    result = await func()
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_exhausted():
    """重试装饰器 - 用尽重试"""

    @retry(max_attempts=2, delay=0.01, exceptions=(ValueError,))
    async def func():
        raise ValueError("permanent error")

    with pytest.raises(ValueError, match="permanent error"):
        await func()


def test_circuit_breaker_states():
    """熔断器状态转换"""
    cb = CircuitBreaker(failure_threshold=3, recovery_time=1.0)
    assert cb.state == "closed"

    # 失败达到阈值
    for _ in range(3):
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("err")))
        except ValueError:
            pass

    assert cb.state == "open"
    assert cb.failure_count == 3


def test_circuit_breaker_open_blocks_calls():
    """熔断器开启时阻止调用"""
    cb = CircuitBreaker(failure_threshold=1, recovery_time=60.0)
    cb._on_failure()
    assert cb.state == "open"

    with pytest.raises(ServiceError, match="服务暂时不可用"):
        cb.call(lambda: "should not execute")
