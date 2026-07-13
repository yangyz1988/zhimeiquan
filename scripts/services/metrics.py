"""Prometheus 指标导出"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# 指标定义
# ─────────────────────────────────────────

# 请求计数
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

# 请求延迟
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# 活跃连接
ACTIVE_CONNECTIONS = Gauge(
    "active_connections",
    "Number of active connections"
)

# 数据库查询延迟
DB_QUERY_LATENCY = Histogram(
    "db_query_duration_seconds",
    "Database query latency",
    ["operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# 缓存命中率
CACHE_HITS = Counter("cache_hits_total", "Total cache hits")
CACHE_MISSES = Counter("cache_misses_total", "Total cache misses")

# 错误计数
ERROR_COUNT = Counter(
    "errors_total",
    "Total errors",
    ["type", "endpoint"]
)


# ─────────────────────────────────────────
# 中间件
# ─────────────────────────────────────────

def metrics_middleware(request, call_next):
    """指标收集中间件"""
    start_time = time.time()
    
    # 增加活跃连接
    ACTIVE_CONNECTIONS.inc()
    
    try:
        response = call_next(request)
        
        # 记录请求
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        # 记录延迟
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(latency)
        
        return response
    
    except Exception as e:
        # 记录错误
        ERROR_COUNT.labels(
            type=type(e).__name__,
            endpoint=request.url.path
        ).inc()
        raise
    
    finally:
        ACTIVE_CONNECTIONS.dec()


# ─────────────────────────────────────────
# 装饰器
# ─────────────────────────────────────────

def track_db_query(operation: str, table: str):
    """数据库查询追踪装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                latency = time.time() - start
                DB_QUERY_LATENCY.labels(
                    operation=operation,
                    table=table
                ).observe(latency)
        return wrapper
    return decorator


def track_cache_hit():
    """缓存命中追踪"""
    CACHE_HITS.inc()


def track_cache_miss():
    """缓存未命中追踪"""
    CACHE_MISSES.inc()


# ─────────────────────────────────────────
# 端点
# ─────────────────────────────────────────

async def metrics_endpoint():
    """Prometheus 指标端点"""
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


# ─────────────────────────────────────────
# 业务指标
# ─────────────────────────────────────────

# 内容统计
CONTENT_TOTAL = Gauge("content_total", "Total content count", ["status"])
CONTENT_PUBLISHED = Counter("content_published_total", "Total published content")
CONTENT_VIEWS = Counter("content_views_total", "Total content views", ["content_id"])

# 用户统计
USER_TOTAL = Gauge("user_total", "Total users")
USER_ACTIVE = Gauge("user_active_total", "Active users in last 24h")
USER_SIGNUPS = Counter("user_signups_total", "Total user signups")

# 订阅统计
SUBSCRIPTION_TOTAL = Gauge("subscription_total", "Total subscriptions", ["plan"])
SUBSCRIPTION_REVENUE = Counter(
    "subscription_revenue_total",
    "Total subscription revenue",
    ["plan"],
    unit="cents"
)

# 热点统计
TRENDS_SCANNED = Counter("trends_scanned_total", "Total trends scanned")
TRENDS_MATCHED = Counter("trends_matched_total", "Total trends matched with content")


def record_content_published():
    CONTENT_PUBLISHED.inc()

def record_content_view(content_id: str):
    CONTENT_VIEWS.labels(content_id=content_id).inc()

def record_user_signup():
    USER_SIGNUPS.inc()

def record_subscription_revenue(plan: str, amount_cents: int):
    SUBSCRIPTION_REVENUE.labels(plan=plan).inc(amount_cents)

def record_trends_scanned(count: int):
    TRENDS_SCANNED.inc(count)

def record_trends_matched(count: int):
    TRENDS_MATCHED.inc(count)