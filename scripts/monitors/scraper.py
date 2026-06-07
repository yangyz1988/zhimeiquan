"""各平台爆款内容采集器 - 支持 10+ 主流平台"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any

import httpx

from services.logging import logger


class PlatformScraper:
    """平台内容采集 - 通过公开 API/网页采集热门内容"""

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

    def __init__(self, timeout: float = 30.0):
        self.client = httpx.AsyncClient(timeout=timeout)
        self._request_count = 0
        self._last_request_time: dict[str, float] = {}

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
        """获取平台热搜/热门内容列表"""
        config = self.PLATFORMS.get(platform)
        if not config:
            return []

        await self._throttle(platform)

        for attempt in range(3):
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
                logger.warning(
                    f"采集 {platform} 失败 (尝试 {attempt + 1}/3)", error=str(e)
                )
                if attempt < 2:
                    await asyncio.sleep(2**attempt)

        return []

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

    def get_supported_platforms(self) -> list[dict[str, str]]:
        """获取所有支持的平台信息"""
        return [
            {
                "name": name,
                "category": cfg.get("category", ""),
            }
            for name, cfg in self.PLATFORMS.items()
        ]
