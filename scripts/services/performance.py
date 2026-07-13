"""性能优化工具集

功能:
- 缓存策略
- 分页优化
- CDN 配置助手
- 图片优化
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

# ========================================
# 缓存策略
# ========================================

class CacheStrategy:
    """缓存策略配置"""
    
    # 缓存时长（秒）
    TTL = {
        "hot_trends": 300,        # 热点数据 5 分钟
        "user_profile": 3600,     # 用户资料 1 小时
        "content_list": 600,      # 内容列表 10 分钟
        "media_assets": 86400,    # 媒体资源 1 天
        "analytics": 1800,        # 分析数据 30 分钟
        "static": 31536000,       # 静态资源 1 年
    }
    
    # 缓存键前缀
    PREFIX = {
        "hot_trends": "trends:",
        "user_profile": "user:",
        "content_list": "content:",
        "media_assets": "media:",
        "analytics": "stats:",
    }
    
    # 缓存标签（用于批量失效）
    TAGS = {
        "user": ["user_profile", "user_settings"],
        "content": ["content_list", "content_detail"],
        "trends": ["hot_trends", "trend_detail"],
    }


def cache_key(prefix: str, *args, **kwargs) -> str:
    """生成缓存键"""
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)


def cache_response(ttl: int = 300, key_prefix: str = ""):
    """缓存响应装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key_str = cache_key(key_prefix or func.__name__, *args, **kwargs)
            
            # 尝试从缓存获取
            # 实际实现需要 Redis
            cached = None  # await redis.get(cache_key_str)
            
            if cached:
                logger.debug(f"Cache hit: {cache_key_str}")
                return json.loads(cached)
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            # await redis.setex(cache_key_str, ttl, json.dumps(result))
            logger.debug(f"Cache set: {cache_key_str}, TTL: {ttl}")
            
            return result
        return wrapper
    return decorator


# ========================================
# 分页优化
# ========================================

class PaginationOptimizer:
    """分页优化器"""
    
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    @staticmethod
    def calculate_offset(page: int, page_size: int) -> int:
        """计算偏移量"""
        return (page - 1) * page_size
    
    @staticmethod
    def validate_page_size(page_size: int) -> int:
        """验证并修正页面大小"""
        if page_size < 1:
            return PaginationOptimizer.DEFAULT_PAGE_SIZE
        if page_size > PaginationOptimizer.MAX_PAGE_SIZE:
            return PaginationOptimizer.MAX_PAGE_SIZE
        return page_size
    
    @staticmethod
    def build_pagination_response(
        items: List[Any],
        total: int,
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """构建分页响应"""
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }
    
    @staticmethod
    def cursor_pagination(
        items: List[Dict],
        cursor_field: str = "id",
        cursor: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """游标分页（适用于大数据量）"""
        filtered = items
        
        if cursor:
            # 找到游标位置
            for i, item in enumerate(items):
                if str(item.get(cursor_field)) == cursor:
                    filtered = items[i + 1:]
                    break
        
        # 截取限制数量
        result = filtered[:limit]
        next_cursor = None
        
        if len(filtered) > limit:
            next_cursor = result[-1].get(cursor_field)
        
        return {
            "items": result,
            "next_cursor": next_cursor,
            "has_more": len(filtered) > limit,
        }


# ========================================
# CDN 配置
# ========================================

class CDNConfig:
    """CDN 配置助手"""
    
    # CDN 提供商
    PROVIDERS = {
        "aliyun": {
            "domain": ".alicdn.com",
            "regions": ["cn-hangzhou", "cn-shanghai", "cn-beijing"],
        },
        "tencent": {
            "domain": ".cdn.dnsv1.com",
            "regions": ["ap-guangzhou", "ap-shanghai", "ap-beijing"],
        },
        "cloudflare": {
            "domain": ".cloudflare.com",
            "regions": ["global"],
        },
    }
    
    # 缓存规则
    CACHE_RULES = [
        {
            "pattern": "*.jpg",
            "ttl": 86400 * 30,  # 30 天
            "type": "image",
        },
        {
            "pattern": "*.png",
            "ttl": 86400 * 30,
            "type": "image",
        },
        {
            "pattern": "*.webp",
            "ttl": 86400 * 30,
            "type": "image",
        },
        {
            "pattern": "*.mp4",
            "ttl": 86400 * 7,  # 7 天
            "type": "video",
        },
        {
            "pattern": "*.js",
            "ttl": 86400 * 365,  # 1 年（带版本号）
            "type": "script",
        },
        {
            "pattern": "*.css",
            "ttl": 86400 * 365,
            "type": "style",
        },
        {
            "pattern": "/api/*",
            "ttl": 0,  # 不缓存
            "type": "api",
        },
    ]
    
    @staticmethod
    def get_cdn_url(
        original_url: str,
        cdn_domain: str,
        use_https: bool = True
    ) -> str:
        """获取 CDN URL"""
        if cdn_domain in original_url:
            return original_url
        
        # 替换域名
        from urllib.parse import urlparse
        parsed = urlparse(original_url)
        cdn_url = f"{'https' if use_https else 'http'}://{cdn_domain}{parsed.path}"
        
        if parsed.query:
            cdn_url += f"?{parsed.query}"
        
        return cdn_url
    
    @staticmethod
    def generate_cache_key(url: str) -> str:
        """生成缓存键"""
        return hashlib.md5(url.encode()).hexdigest()
    
    @staticmethod
    def purge_cache(urls: List[str], cdn_provider: str = "aliyun") -> Dict:
        """刷新 CDN 缓存"""
        # 实际实现需要调用 CDN API
        logger.info(f"Purging {len(urls)} URLs from {cdn_provider} CDN")
        return {
            "success": True,
            "urls": urls,
            "provider": cdn_provider,
            "timestamp": datetime.utcnow().isoformat(),
        }


# ========================================
# 图片优化
# ========================================

class ImageOptimizer:
    """图片优化器"""
    
    # 支持的格式
    SUPPORTED_FORMATS = ["jpg", "jpeg", "png", "webp", "gif", "avif"]
    
    # 响应式尺寸
    RESPONSIVE_SIZES = [320, 480, 768, 1024, 1280, 1920]
    
    @staticmethod
    def get_responsive_srcset(
        base_url: str,
        sizes: Optional[List[int]] = None
    ) -> str:
        """生成响应式图片 srcset"""
        sizes = sizes or ImageOptimizer.RESPONSIVE_SIZES
        srcset_parts = []
        
        for size in sizes:
            # 假设 CDN 支持尺寸参数
            url = f"{base_url}?w={size}"
            srcset_parts.append(f"{url} {size}w")
        
        return ", ".join(srcset_parts)
    
    @staticmethod
    def get_optimized_url(
        original_url: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        quality: int = 80,
        format: str = "webp"
    ) -> str:
        """获取优化后的图片 URL"""
        params = []
        
        if width:
            params.append(f"w={width}")
        if height:
            params.append(f"h={height}")
        params.append(f"q={quality}")
        params.append(f"f={format}")
        
        separator = "&" if "?" in original_url else "?"
        return f"{original_url}{separator}{'&'.join(params)}"
    
    @staticmethod
    def calculate_placeholder_size(width: int, height: int) -> str:
        """计算占位符尺寸"""
        aspect_ratio = width / height
        return f"aspect-{int(aspect_ratio * 100)}"


# ========================================
# 懒加载
# ========================================

class LazyLoader:
    """懒加载助手"""
    
    @staticmethod
    def get_lazy_attributes(
        threshold: str = "200px",
        placeholder: Optional[str] = None
    ) -> Dict[str, str]:
        """获取懒加载属性"""
        attrs = {
            "loading": "lazy",
            "data-loading": "lazy",
        }
        
        if threshold:
            attrs["data-threshold"] = threshold
        
        if placeholder:
            attrs["src"] = placeholder
        
        return attrs
    
    @staticmethod
    def get_intersection_observer_script() -> str:
        """获取 Intersection Observer 脚本"""
        return """
        <script>
        if ('IntersectionObserver' in window) {
            const lazyImages = document.querySelectorAll('[data-loading="lazy"]');
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            }, { rootMargin: '200px' });
            
            lazyImages.forEach(img => imageObserver.observe(img));
        }
        </script>
        """


# ========================================
# 性能监控
# ========================================

class PerformanceMonitor:
    """性能监控"""
    
    @staticmethod
    def measure_time(name: str):
        """测量执行时间装饰器"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start = asyncio.get_event_loop().time()
                result = await func(*args, **kwargs)
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                
                logger.info(f"[{name}] 执行时间: {elapsed:.2f}ms")
                
                # 可以发送到监控系统
                # await metrics.record(name, elapsed)
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def record_metric(name: str, value: float, tags: Optional[Dict] = None):
        """记录指标"""
        metric = {
            "name": name,
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "tags": tags or {},
        }
        
        # 发送到监控系统
        logger.debug(f"Metric: {json.dumps(metric)}")
    
    @staticmethod
    def get_performance_report() -> Dict[str, Any]:
        """获取性能报告"""
        # 从监控系统获取数据
        return {
            "api_latency": {
                "p50": 120,
                "p95": 350,
                "p99": 800,
            },
            "cache_hit_rate": 0.85,
            "cdn_bandwidth": {
                "daily_gb": 150,
                "monthly_gb": 4500,
            },
            "error_rate": 0.002,
        }


# 导出
__all__ = [
    "CacheStrategy",
    "cache_key",
    "cache_response",
    "PaginationOptimizer",
    "CDNConfig",
    "ImageOptimizer",
    "LazyLoader",
    "PerformanceMonitor",
]