"""统一分页 + 内存限流工具模块

提供:
    - PaginationHelper  — 通用分页计算
    - PaginatedResponse  — 统一分页响应 TypedDict
    - RateLimiter        — 基于内存的简单限流（与 cache.py 中的 Redis
                           限流互补，适用于无 Redis 依赖的轻量场景）
"""

import time
from dataclasses import dataclass, field
from math import ceil
from typing import Any, TypedDict


# =============================================================================
# 分页响应类型
# =============================================================================


class PaginatedResponse(TypedDict):
    """统一的分页响应格式"""

    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# =============================================================================
# PaginationHelper
# =============================================================================


@dataclass
class PaginationConfig:
    """分页配置（可按需覆盖默认值）"""

    default_page: int = 1
    default_page_size: int = 20
    max_page_size: int = 100
    min_page_size: int = 1


class PaginationHelper:
    """通用分页工具

    使用示例:
        >>> helper = PaginationHelper()
        >>> result = helper.paginate(all_items, page=2, page_size=10)
        >>> result["total_pages"]
        5

        >>> # 边界保护：page=0 自动修正为 1
        >>> helper.paginate(items, page=0)
    """

    def __init__(self, config: PaginationConfig | None = None) -> None:
        self.config = config or PaginationConfig()

    # -----------------------------------------------------------------
    # 公开 API
    # -----------------------------------------------------------------

    def paginate(
        self,
        items: list[Any],
        page: int | None = None,
        page_size: int | None = None,
    ) -> PaginatedResponse:
        """对列表进行分页并返回统一格式的分页结果。

        Args:
            items:     原始数据列表。
            page:      请求的页码，默认使用 config.default_page。
            page_size: 每页条数，默认使用 config.default_page_size。

        Returns:
            PaginatedResponse — 包含 items / total / page / page_size /
                                 total_pages / has_next / has_prev。
        """
        # --- 参数规范化 ---
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)
        total = len(items)

        # 总页数至少为 1，避免 total=0 时除数为零
        total_pages = max(1, ceil(total / page_size))

        # 页码钳位
        page = self._clamp_page(page, total_pages)

        # 切片
        start = (page - 1) * page_size
        stop = start + page_size
        paged_items = items[start:stop]

        return self._build_response(
            items=paged_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # -----------------------------------------------------------------
    # 内部方法
    # -----------------------------------------------------------------

    def _normalize_page(self, page: int | None) -> int:
        """校验并规范化页码（None / 0 / 负数 均回退到默认值）。"""
        if page is None or page < 1:
            return self.config.default_page
        return page

    def _normalize_page_size(self, page_size: int | None) -> int:
        """校验并规范化每页条数（钳位到 [min_page_size, max_page_size]）。"""
        if page_size is None:
            return self.config.default_page_size
        return max(
            self.config.min_page_size,
            min(page_size, self.config.max_page_size),
        )

    @staticmethod
    def _clamp_page(page: int, total_pages: int) -> int:
        """将页码钳位到 [1, total_pages] 区间。"""
        if page > total_pages:
            return total_pages
        return page

    @staticmethod
    def _build_response(
        items: list[Any],
        total: int,
        page: int,
        page_size: int,
        total_pages: int,
    ) -> PaginatedResponse:
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }


# =============================================================================
# RateLimiter（内存版）
# =============================================================================


class RateLimiter:
    """基于内存的轻量限流器（滑动窗口算法）。

    与 ``cache.RateLimiter`` 的区别：
        - cache.RateLimiter 优先 Redis，降级为内存；本类**纯内存**，零依赖。
        - 适用于单进程部署、无 Redis 环境或不需要持久化限流的场景。

    使用示例:
        >>> limiter = RateLimiter()
        >>> limiter.check_limit("user_123", max_requests=10, window_seconds=60)
        True   # 允许通过

        >>> # 快速连续调用 11 次（同一 key 同一窗口内）
        >>> limiter.check_limit("user_123", max_requests=10, window_seconds=60)
        False  # 触发限流
    """

    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = {}
        self._max_entries: int = 10_000  # 防止内存泄漏

    # -----------------------------------------------------------------
    # 公开 API
    # -----------------------------------------------------------------

    def check_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> bool:
        """检查是否允许本次请求通过。

        Args:
            key:             限流键（如用户 ID、IP、接口路径）。
            max_requests:    时间窗口内允许的最大请求数。
            window_seconds:  滑动窗口大小（秒）。

        Returns:
            True  — 允许通过。
            False — 触发限流，应拒绝请求。
        """
        now = time.monotonic()
        cutoff = now - window_seconds

        # 获取或初始化时间戳列表
        timestamps = self._requests.get(key)
        if timestamps is None:
            self._requests[key] = [now]
            self._maybe_evict()
            return True

        # 滑动窗口清理过期记录
        timestamps[:] = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= max_requests:
            # 已达上限，拒绝（不记录本次时间戳）
            return False

        timestamps.append(now)
        self._maybe_evict()
        return True

    def remaining(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> int:
        """返回当前窗口内还可发送的请求数。

        Args:
            key:             限流键。
            max_requests:    窗口上限。
            window_seconds:  窗口大小。

        Returns:
            剩余允许次数（0 表示已触发限流）。
        """
        now = time.monotonic()
        cutoff = now - window_seconds

        timestamps = self._requests.get(key, [])
        timestamps[:] = [t for t in timestamps if t > cutoff]

        used = len(timestamps)
        return max(0, max_requests - used)

    def reset(self, key: str | None = None) -> None:
        """重置限流状态。

        Args:
            key: 指定要重置的键，None 表示重置全部。
        """
        if key is None:
            self._requests.clear()
        else:
            self._requests.pop(key, None)

    # -----------------------------------------------------------------
    # 内部方法
    # -----------------------------------------------------------------

    def _maybe_evict(self) -> None:
        """当存储的 key 数量超过阈值时，清理最老的条目（防止内存泄漏）。"""
        if len(self._requests) <= self._max_entries:
            return

        # 按每个 key 最新活跃时间排序，淘汰最不活跃的 20%
        sorted_keys = sorted(
            self._requests.keys(),
            key=lambda k: max(self._requests[k]) if self._requests[k] else 0,
        )
        remove_count = int(len(sorted_keys) * 0.2)
        # 至少清理 10 个，避免微幅超过阈值时频繁清理
        remove_count = max(remove_count, 10)

        for k in sorted_keys[:remove_count]:
            del self._requests[k]


# =============================================================================
# 模块级默认实例
# =============================================================================

_default_pagination = PaginationHelper()
_default_rate_limiter = RateLimiter()


def paginate(
    items: list[Any],
    page: int | None = None,
    page_size: int | None = None,
) -> PaginatedResponse:
    """便捷函数 — 使用默认 PaginationHelper 实例进行分页。"""
    return _default_pagination.paginate(items, page=page, page_size=page_size)


def check_limit(
    key: str,
    max_requests: int,
    window_seconds: int = 60,
) -> bool:
    """便捷函数 — 使用默认 RateLimiter 实例检查限流。"""
    return _default_rate_limiter.check_limit(key, max_requests, window_seconds)
