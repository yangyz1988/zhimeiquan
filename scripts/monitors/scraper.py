"""各平台爆款内容采集器"""

import json
import time
from datetime import datetime
from typing import Any

import httpx


class PlatformScraper:
    """平台内容采集 - 通过公开 API/网页采集热门内容"""

    PLATFORMS = {
        "抖音": {
            "hot_api": "https://www.douyin.com/aweme/v1/web/hot/search/list/",
            "trending_api": "https://www.douyin.com/aweme/v1/web/discover/search/",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.douyin.com/",
            },
        },
        "小红书": {
            "hot_api": "https://edith.xiaohongshu.com/api/sns/v1/search/hot_list",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
        },
        "B站": {
            "hot_api": "https://api.bilibili.com/x/web-interface/ranking/v2",
            "trending_api": "https://api.bilibili.com/x/web-interface/search/trending",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
        },
        "微博": {
            "hot_api": "https://weibo.com/ajax/side/hotSearch",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
        },
        "知乎": {
            "hot_api": "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
        },
        "头条": {
            "hot_api": "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
        },
    }

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def fetch_hot_list(self, platform: str) -> list[dict[str, Any]]:
        """获取平台热搜/热门内容列表"""
        config = self.PLATFORMS.get(platform)
        if not config:
            return []

        try:
            resp = await self.client.get(
                config["hot_api"],
                headers=config.get("headers", {}),
            )
            resp.raise_for_status()
            data = resp.json()
            return self._parse_hot_list(platform, data)
        except Exception as e:
            print(f"[Scraper] {platform} 采集失败: {e}")
            return []

    def _parse_hot_list(self, platform: str, data: dict) -> list[dict]:
        """解析各平台热搜数据"""
        results = []

        if platform == "抖音":
            word_list = data.get("data", {}).get("word_list", [])
            for item in word_list[:20]:
                results.append(
                    {
                        "title": item.get("word", ""),
                        "heat": item.get("hot_value", 0),
                        "tag": item.get("word_type", ""),
                        "platform": platform,
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
                    }
                )

        return results

    async def fetch_all_platforms(self) -> dict[str, list[dict]]:
        """并发采集所有平台热搜"""
        results = {}
        for platform in self.PLATFORMS:
            hot_list = await self.fetch_hot_list(platform)
            results[platform] = hot_list
            await asyncio.sleep(1)  # 避免请求过快
        return results


import asyncio
