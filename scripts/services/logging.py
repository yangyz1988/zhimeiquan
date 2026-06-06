"""日志服务 - 结构化日志 + 性能追踪"""

import json
import logging
import os
import sys
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any


class StructuredLogger:
    """结构化日志"""

    def __init__(self, name: str = "zhimeiquan"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            self._setup()

    def _setup(self):
        handler = logging.StreamHandler(sys.stdout)

        if os.getenv("LOG_FORMAT", "json") == "json":
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )

        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

    def _log(self, level: str, message: str, **fields: Any):
        extra = {"fields": fields} if fields else {}
        getattr(self.logger, level)(message, extra=extra)

    def debug(self, message: str, **fields):
        self._log("debug", message, **fields)

    def info(self, message: str, **fields):
        self._log("info", message, **fields)

    def warning(self, message: str, **fields):
        self._log("warning", message, **fields)

    def error(self, message: str, **fields):
        self._log("error", message, **fields)

    def exception(self, message: str, **fields):
        self._log("error", message, **fields)


class JsonFormatter(logging.Formatter):
    """JSON 日志格式"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "fields") and record.fields:
            log_data.update(record.fields)
        return json.dumps(log_data, ensure_ascii=False)


logger = StructuredLogger()


@contextmanager
def track_time(operation: str, **fields: Any):
    """追踪操作耗时"""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        logger.info(
            f"{operation} 完成",
            duration_ms=round(duration * 1000),
            operation=operation,
            **fields,
        )


def log_call(func):
    """装饰器 - 记录函数调用"""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        with track_time(func.__name__):
            try:
                result = await func(*args, **kwargs)
                logger.info(f"{func.__name__} 成功", function=func.__name__)
                return result
            except Exception as e:
                logger.error(
                    f"{func.__name__} 失败", function=func.__name__, error=str(e)
                )
                raise

    return async_wrapper
