"""
Prometheus 风格指标收集
轻量级实现，无需额外依赖
"""

import time
import threading
from collections import defaultdict
from typing import Dict, Any


class MetricsCollector:
    """指标收集器 - 线程安全"""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = defaultdict(list)
        self._start_time = time.time()

    # ---- Counter ----
    def inc(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """计数器递增"""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value

    # ---- Gauge ----
    def set(self, name: str, value: float, labels: Dict[str, str] = None):
        """设置仪表值"""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def gauge_inc(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        """仪表值递增"""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = self._gauges.get(key, 0) + value

    def gauge_dec(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        """仪表值递减"""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = self._gauges.get(key, 0) - value

    # ---- Histogram (简化版) ----
    def observe(self, name: str, value: float, labels: Dict[str, str] = None):
        """记录观测值"""
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
            # 只保留最近 1000 个数据点
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]

    # ---- Export ----
    def export(self) -> Dict[str, Any]:
        """导出所有指标（JSON格式）"""
        with self._lock:
            uptime = time.time() - self._start_time

            # 计算直方图统计
            hist_stats = {}
            for key, values in self._histograms.items():
                if values:
                    hist_stats[key] = {
                        "count": len(values),
                        "sum": sum(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                    }

            return {
                "uptime_seconds": round(uptime, 2),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": hist_stats,
            }

    def export_prometheus(self) -> str:
        """导出 Prometheus 文本格式"""
        data = self.export()
        lines = []

        lines.append(f"# HELP uptime_seconds Service uptime in seconds")
        lines.append(f"# TYPE uptime_seconds gauge")
        lines.append(f"uptime_seconds {data['uptime_seconds']}")

        for key, value in data["counters"].items():
            lines.append(f"# HELP {key} Counter metric")
            lines.append(f"# TYPE {key} counter")
            lines.append(f"{key} {value}")

        for key, value in data["gauges"].items():
            lines.append(f"# HELP {key} Gauge metric")
            lines.append(f"# TYPE {key} gauge")
            lines.append(f"{key} {value}")

        return "\n".join(lines)

    @staticmethod
    def _make_key(name: str, labels: Dict[str, str] = None) -> str:
        """生成带标签的指标名"""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f'{name}{{{label_str}}}'


# 全局单例
metrics = MetricsCollector()


# 便捷装饰器：统计接口耗时
def timed(metric_name: str = "http_request_duration_seconds"):
    """请求耗时统计装饰器"""
    def decorator(func):
        import functools

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                metrics.inc("http_requests_total", labels={"status": "success"})
                return result
            except Exception:
                metrics.inc("http_requests_total", labels={"status": "error"})
                raise
            finally:
                duration = time.time() - start
                metrics.observe(metric_name, duration)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                metrics.inc("http_requests_total", labels={"status": "success"})
                return result
            except Exception:
                metrics.inc("http_requests_total", labels={"status": "error"})
                raise
            finally:
                duration = time.time() - start
                metrics.observe(metric_name, duration)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
