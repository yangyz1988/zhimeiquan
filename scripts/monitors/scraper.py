"""各平台爆款内容采集器 - 支持 10+ 主流平台

采集策略（三级降级）：
1. 浏览器采集（优先） — 通过 Playwright 渲染页面，获取真实热门数据
2. HTTP API 采集 — 直接请求公开 API（保留原有逻辑）
3. 静态规则 fallback — 从 data/rules/ 加载本地规则文件
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from services.logging import logger


class PlatformScraper:
    """平台内容采集 - 浏览器优先，HTTP 降级，静态 fallback"""

    PLATFORMS: dict[str, dict[str, Any]] = {
        "抖音": {
            "hot_api": "https://www.douyin.com/aweme/v1/web/hot/search/list/",
            "trending_api": "https://www.douyin.com/aweme/v1/web/discover/search/",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.douyin.com/",
            },
            "category": "短视频",
        },
        "小红书": {
            "hot_api": "https://edith.xiaohongshu.com/api/sns/v1/search/hot_list",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            "category": "种草",
        },
        "B站": {
            "hot_api": "https://api.bilibili.com/x/web-interface/ranking/v2",
            "trending_api": "https://api.bilibili.com/x/web-interface/search/trending",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            "category": "中长视频",
        },
        "微博": {
            "hot_api": "https://weibo.com/ajax/side/hotSearch",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            "category": "社交",
        },
        "知乎": {
            "hot_api": "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            "category": "问答",
        },
        "头条": {
            "hot_api": "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            "category": "资讯",
        },
        "快手": {
            "hot_api": "https://www.kuaishou.com/graphql",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            "category": "短视频",
        },
        "YouTube": {
            "hot_api": "https://www.youtube.com/feed/trending",
            "trending_api": "https://www.youtube.com/feed/explore/trending",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            "category": "中长视频",
        },
        "TikTok": {
            "hot_api": "https://www.tiktok.com/api/recommend/item_list/",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            "category": "短视频",
        },
        "公众号": {
            "hot_api": "https://weixin.sogou.com/api/search?type=2&query=热门",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            "category": "图文",
        },
        "视频号": {
            "hot_api": "https://channels.weixin.qq.com/cgi-bin/mmfind-bin/search",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            "category": "短视频",
        },
        "百度热搜": {
            "hot_api": "https://top.baidu.com/board?tab=realtime",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            "category": "资讯",
        },
    }

    def __init__(self, timeout: float = 30.0, rules_dir: str = "../data/rules", use_browser: bool = True):
        self.client = httpx.AsyncClient(timeout=timeout)
        self._request_count = 0
        self._last_request_time: dict[str, float] = {}
        self._rules_dir = Path(rules_dir)
        self._fallback_loaded: set[str] = set()
        self._use_browser = use_browser and os.getenv("BROWSER_SCRAPE_ENABLED", "true").lower() == "true"

    async def close(self):
        await self.client.aclose()

    async def _throttle(self, platform: str, min_interval: float = 1.0):
        """限流：避免请求过快"""
        last = self._last_request_time.get(platform, 0)
        elapsed = time.time() - last
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        self._last_request_time[platform] = time.time()
        self._request_count += 1

    async def fetch_hot_list(self, platform: str) -> list[dict[str, Any]]:
        """获取平台热搜/热门内容列表。

        采集策略（三级降级）：
        1. 浏览器采集（优先）— 通过 Playwright 渲染页面
        2. HTTP API 采集 — 原有逻辑
        3. 静态规则 fallback — 本地文件
        """
        config = self.PLATFORMS.get(platform)
        if not config:
            return []

        await self._throttle(platform)

        # === 第一优先级：浏览器采集 ===
        if self._use_browser:
            try:
                result = await self._fetch_via_browser(platform)
                if result and result.get("success") and result.get("hot_items"):
                    logger.info(
                        f"{platform} 浏览器采集成功",
                        count=len(result["hot_items"]),
                        topics=len(result.get("topics", [])),
                    )
                    return result["hot_items"]
            except Exception as e:
                logger.warning(f"浏览器采集 {platform} 失败，降级到 HTTP API", error=str(e))

        # === 第二优先级：HTTP API（原有逻辑） ===
        max_retries = 4
        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                resp = await self.client.get(
                    config["hot_api"],
                    headers=config.get("headers", {}),
                )
                resp.raise_for_status()
                data = resp.json()
                results = self._parse_hot_list(platform, data)
                if results:
                    return results
            except Exception as e:
                last_error = e
                logger.warning(
                    f"采集 {platform} 失败 (尝试 {attempt + 1}/{max_retries})",
                    error=str(e),
                )
                if attempt < max_retries - 1:
                    backoff = 0.5 * (2**attempt)
                    await asyncio.sleep(backoff)

        # 所有 API 重试均失败 -> 使用静态 fallback
        logger.warning(
            f"{platform} API 全部失败 ({max_retries}次), 使用静态规则 fallback",
            error=str(last_error),
        )
        return self._load_fallback(platform)

    def _parse_hot_list(self, platform: str, data: Any) -> list[dict]:
        """解析各平台热搜数据"""
        if not isinstance(data, dict):
            return []

        results: list[dict] = []
        category = self.PLATFORMS.get(platform, {}).get("category", "")

        if platform == "抖音":
            word_list = data.get("data", {}).get("word_list", [])
            for item in word_list[:20]:
                results.append(
                    {
                        "title": item.get("word", ""),
                        "heat": item.get("hot_value", 0),
                        "tag": item.get("word_type", ""),
                        "platform": platform,
                        "category": category,
                    }
                )

        elif platform == "B站":
            data_list = data.get("data", {}).get("list", [])
            for item in data_list[:20]:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "heat": item.get("stat", {}).get("view", 0),
                        "tag": item.get("tname", ""),
                        "platform": platform,
                        "category": category,
                    }
                )

        elif platform == "微博":
            data_list = data.get("data", {}).get("realtime", [])
            for item in data_list[:20]:
                results.append(
                    {
                        "title": item.get("note", ""),
                        "heat": item.get("num", 0),
                        "tag": item.get("category", ""),
                        "platform": platform,
                        "category": category,
                    }
                )

        elif platform == "知乎":
            data_list = data.get("data", [])
            for item in data_list[:20]:
                target = item.get("target", {})
                results.append(
                    {
                        "title": target.get("title", ""),
                        "heat": item.get("detail_text", ""),
                        "tag": "热点",
                        "platform": platform,
                        "category": category,
                    }
                )

        elif platform == "头条":
            data_list = data.get("data", [])
            for item in data_list[:20]:
                results.append(
                    {
                        "title": item.get("Title", ""),
                        "heat": item.get("HotValue", 0),
                        "tag": item.get("Category", ""),
                        "platform": platform,
                        "category": category,
                    }
                )

        elif platform == "百度热搜":
            data_list = data.get("data", {}).get("cards", [{}])[0].get("content", [])
            for item in data_list[:20]:
                results.append(
                    {
                        "title": item.get("word", ""),
                        "heat": item.get("hotScore", 0),
                        "tag": item.get("desc", ""),
                        "platform": platform,
                        "category": category,
                    }
                )

        elif platform == "小红书":
            data_list = data.get("data", {}).get("items", [])
            for item in data_list[:20]:
                results.append(
                    {
                        "title": item.get("title", item.get("word", "")),
                        "heat": item.get("score", 0),
                        "tag": item.get("type", ""),
                        "platform": platform,
                        "category": category,
                    }
                )

        elif platform == "快手":
            items = data.get("data", {}).get("visionVideoList", [])
            for item in items[:20]:
                photo = item.get("photo", {})
                results.append(
                    {
                        "title": photo.get("caption", ""),
                        "heat": photo.get("viewCount", 0),
                        "tag": "热门",
                        "platform": platform,
                        "category": category,
                    }
                )

        elif platform == "YouTube":
            items = data.get("contents", [])
            for section in items[:5]:
                for item in section.get("items", [])[:5]:
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "heat": item.get("view_count", "0"),
                            "tag": "热门",
                            "platform": platform,
                            "category": category,
                        }
                    )

        elif platform == "TikTok":
            items = data.get("itemList", [])
            for item in items[:20]:
                results.append(
                    {
                        "title": item.get("desc", ""),
                        "heat": item.get("stats", {}).get("playCount", 0),
                        "tag": "推荐",
                        "platform": platform,
                        "category": category,
                    }
                )

        elif platform == "公众号":
            items = data.get("items", [])
            for item in items[:20]:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "heat": 0,
                        "tag": "热门",
                        "platform": platform,
                        "category": category,
                    }
                )

        elif platform == "视频号":
            items = data.get("data", {}).get("feeds", [])
            for item in items[:20]:
                media = item.get("media", {})
                results.append(
                    {
                        "title": media.get("description", media.get("title", "")),
                        "heat": item.get("viewCount", 0),
                        "tag": "推荐",
                        "platform": platform,
                        "category": category,
                    }
                )

        return [r for r in results if r.get("title")]

    async def fetch_all_platforms(
        self, platforms: list[str] | None = None
    ) -> dict[str, list[dict]]:
        """并发采集所有/指定平台热搜"""
        targets = platforms or list(self.PLATFORMS.keys())
        results: dict[str, list[dict]] = {}

        # 并发采集
        tasks = [self.fetch_hot_list(p) for p in targets]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)

        for platform, result in zip(targets, gathered):
            if isinstance(result, Exception):
                logger.error(f"{platform} 采集异常", error=str(result))
                results[platform] = []
            else:
                results[platform] = result

        return results

    async def _fetch_via_browser(self, platform: str) -> dict[str, Any] | None:
        """通过浏览器采集平台热门数据（新增）。

        调用 monitors.browser.PlatformBrowser 进行渲染级采集，
        返回格式与现有 fetch_hot_list 兼容的 hot_items 列表。
        """
        try:
            from monitors.browser import get_browser_pool, PlatformBrowser, is_browser_enabled
            from monitors.parser import HotContentParser

            if not is_browser_enabled():
                return None

            pool = await get_browser_pool()
            pb = PlatformBrowser(pool)
            result = await pb.scrape_platform(platform)

            if not result.success:
                return None

            # 转换为兼容格式
            hot_items = []
            category = self.PLATFORMS.get(platform, {}).get("category", "")
            for i, title in enumerate(result.raw_titles[:50]):
                hot_items.append({
                    "title": title,
                    "heat": 0,
                    "tag": result.topics[0] if result.topics else "热门",
                    "platform": platform,
                    "category": category,
                    "source": "browser",
                })

            return {
                "success": True,
                "hot_items": hot_items,
                "topics": result.topics,
                "raw_titles": result.raw_titles,
                "collected_at": result.collected_at,
            }
        except ImportError:
            logger.debug("playwright 未安装，跳过浏览器采集")
            return None
        except Exception as e:
            logger.warning(f"浏览器采集 {platform} 异常: {e}")
            return None

    def _load_fallback(self, platform: str) -> list[dict[str, Any]]:
        """API 全部失败时使用静态规则文件作为 fallback"""
        rule_file = self._rules_dir / f"{platform}.json"
        if not rule_file.exists():
            logger.warning(f"fallback 规则文件不存在: {rule_file}")
            return []

        try:
            with open(rule_file, "r", encoding="utf-8") as f:
                rules = json.load(f)

            trending = rules.get("trending_topics", [])
            category = self.PLATFORMS.get(platform, {}).get("category", "")
            results = []
            for topic in trending:
                if isinstance(topic, str):
                    results.append({
                        "title": topic,
                        "heat": 0,
                        "tag": "热门",
                        "platform": platform,
                        "category": category,
                        "fallback": True,
                    })
                elif isinstance(topic, dict):
                    results.append({
                        "title": topic.get("title", topic.get("word", "")),
                        "heat": topic.get("hot_value", topic.get("heat", 0)),
                        "tag": topic.get("tag", "热门"),
                        "platform": platform,
                        "category": category,
                        "fallback": True,
                    })

            self._fallback_loaded.add(platform)
            logger.info(
                f"使用静态 fallback 返回 {platform} 共 {len(results)} 条",
            )
            return results[:20]
        except Exception as e:
            logger.exception(f"加载 fallback 规则失败: {platform}")
            return []

    def get_source_health(self) -> dict:
        """获取各平台数据源健康状态。

        返回每个平台的数据来源级别（browser/api/fallback）和新
        鲜度信息，供前端展示数据可信度。

        Returns:
            {
                "platforms": {
                    "抖音": {"source": "browser", "fresh": true, "last_updated": "..."},
                    ...
                },
                "summary": {"browser": 3, "api": 5, "fallback": 5, "total": 13},
            }
        """
        from datetime import datetime, timezone, timedelta

        platforms_health = {}
        summary = {"browser": 0, "api": 0, "fallback": 0, "total": 0}
        now = datetime.now(timezone.utc)

        for platform in self.PLATFORMS:
            rule_file = self._rules_dir / f"{platform}.json"
            last_updated = ""
            source = "unknown"
            fresh = False

            if rule_file.exists():
                try:
                    with open(rule_file, "r", encoding="utf-8") as f:
                        rules = json.load(f)
                    last_updated = rules.get("last_updated", rules.get("updated_at", ""))
                    if last_updated:
                        try:
                            updated = datetime.fromisoformat(last_updated)
                            fresh = (now - updated) < timedelta(hours=12)
                        except (ValueError, TypeError):
                            pass

                    # 判断数据来源
                    if rules.get("is_seed"):
                        source = "seed"
                    elif platform in self._fallback_loaded:
                        source = "fallback"
                    else:
                        source = "api"  # 或 browser，通过文件中的 source 字段判断
                        # 检查文件中是否有 source 标记
                        if "source" in rules:
                            source = rules["source"]
                except (json.JSONDecodeError, OSError):
                    source = "error"
            else:
                source = "missing"

            platforms_health[platform] = {
                "source": source,
                "fresh": fresh,
                "last_updated": last_updated,
                "category": self.PLATFORMS[platform].get("category", ""),
            }
            summary[source] = summary.get(source, 0) + 1
            summary["total"] += 1

        return {"platforms": platforms_health, "summary": summary}

    def get_health_metrics(self) -> dict[str, Any]:
        """返回采集器健康指标"""
        metrics: dict[str, Any] = {
            "request_count": self._request_count,
            "fallback_count": len(self._fallback_loaded),
            "fallback_platforms": sorted(self._fallback_loaded),
            "last_requests": {
                k: datetime.fromtimestamp(v).isoformat()
                for k, v in self._last_request_time.items()
            },
            "browser_enabled": self._use_browser,
        }
        # 尝试获取浏览器池健康状态
        try:
            from monitors.browser import _browser_pool
            if _browser_pool is not None:
                metrics["browser"] = _browser_pool.health()
        except Exception:
            pass
        return metrics

    def get_supported_platforms(self) -> list[dict[str, str]]:
        """获取所有支持的平台信息"""
        return [
            {
                "name": name,
                "category": cfg.get("category", ""),
            }
            for name, cfg in self.PLATFORMS.items()
        ]
