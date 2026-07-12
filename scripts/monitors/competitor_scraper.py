"""竞品内容自动爬取 — 定时扫描对标账号最新发布

通过 Playwright 定期访问竞品主页，抓取最新发布内容。
与 CompetitorMonitor 集成，自动录入采集到的内容。

典型用法:
    pool = await get_browser_pool()
    scraper = CompetitorScraper(pool, competitor_monitor)
    results = await scraper.scrape_competitor(competitor)
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Any

from services.logging import logger


class CompetitorScraper:
    """竞品内容自动采集器。

    平台特定逻辑由 STRATEGIES dict 驱动。
    支持平台：抖音、B站、微博、知乎、YouTube、小红书（部分）
    """

    STRATEGIES: dict[str, dict[str, Any]] = {
        "抖音": {
            "profile_url_tpl": "https://www.douyin.com/user/{account_id}",
            "post_selector": ".video-card, .aweme-item",
            "title_selector": ".title, .aweme-title",
            "metrics_selectors": {
                "likes": ".like-count, .digg-count",
                "comments": ".comment-count",
                "shares": ".share-count",
            },
        },
        "B站": {
            "profile_url_tpl": "https://space.bilibili.com/{account_id}/video",
            "post_selector": ".video-card, .cube-list .video-item",
            "title_selector": ".title, .video-title",
            "metrics_selectors": {
                "views": ".play-count, .count",
                "likes": ".like-count",
                "comments": ".comment-count",
            },
        },
        "微博": {
            "profile_url_tpl": "https://weibo.com/u/{account_id}",
            "post_selector": ".WB_cardwrap, .card-wrap",
            "title_selector": ".WB_text, .txt",
            "metrics_selectors": {
                "likes": ".W_icon_click",
                "comments": ".W_icon_comment",
                "shares": ".W_icon_forward",
            },
        },
        "知乎": {
            "profile_url_tpl": "https://www.zhihu.com/people/{account_id}",
            "post_selector": ".ContentItem, .List-item",
            "title_selector": ".ContentItem-title, .RichText",
            "metrics_selectors": {
                "likes": ".VoteButton--up",
                "comments": ".ContentItem-actions button",
            },
        },
        "YouTube": {
            "profile_url_tpl": "https://www.youtube.com/@{account_id}/videos",
            "post_selector": "ytd-rich-item-renderer",
            "title_selector": "#video-title",
            "metrics_selectors": {
                "views": "#metadata-line span:nth-child(1)",
            },
        },
        "小红书": {
            "profile_url_tpl": "https://www.xiaohongshu.com/user/profile/{account_id}",
            "post_selector": ".note-item",
            "title_selector": ".title, .note-title",
            "metrics_selectors": {
                "likes": ".like-count, .count",
            },
        },
    }

    def __init__(self, pool: Any, competitor_monitor: Any):
        """初始化。

        Args:
            pool: BrowserPool 实例
            competitor_monitor: CompetitorMonitor 实例
        """
        self._pool = pool
        self._monitor = competitor_monitor
        self._max_items = int(os.getenv("COMPETITOR_CRAWL_MAX_ITEMS", "20"))

    async def scrape_competitor(self, competitor: dict) -> list[dict]:
        """爬取一个竞品的最新内容列表。

        Args:
            competitor: CompetitorMonitor 中的竞品记录，需含 id/account_id/platform 字段

        Returns:
            可录入 CompetitorMonitor 的 content_data 列表
        """
        platform = competitor.get("platform", "")
        account_id = competitor.get("account_id", "")
        strategy = self.STRATEGIES.get(platform)

        if not strategy:
            logger.warning(f"竞品爬取不支持平台: {platform}")
            return []

        url = strategy["profile_url_tpl"].format(account_id=account_id)
        contents: list[dict] = []

        try:
            async with self._pool.acquire_page() as page:
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # 等待帖子列表
                post_selector = strategy.get("post_selector", ".item")
                try:
                    await page.wait_for_selector(post_selector, timeout=15000)
                except Exception:
                    pass

                # 滚动加载
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 800)")
                    await asyncio.sleep(1.5)

                # 提取内容
                posts = await page.query_selector_all(post_selector)
                for i, post in enumerate(posts[:self._max_items]):
                    try:
                        content_data = await self._extract_post(post, platform, strategy)
                        if content_data.get("title"):
                            contents.append(content_data)
                    except Exception:
                        continue

                logger.info(
                    f"竞品爬取完成: {competitor.get('account_name', account_id)}",
                    platform=platform,
                    found=len(contents),
                )

        except Exception as e:
            logger.warning(
                f"竞品爬取失败: {competitor.get('account_name', account_id)}",
                platform=platform,
                error=str(e),
            )

        # 自动录入 CompetitorMonitor
        recorded = []
        for content in contents:
            try:
                result = self._monitor.record_content(competitor["id"], content)
                if "error" not in result:
                    recorded.append(content)
            except Exception as e:
                logger.debug(f"竞品内容录入跳过（可能重复）: {e}")

        return recorded

    async def scrape_all_for_user(self, user_id: str) -> dict[str, list[dict]]:
        """爬取用户关注的所有竞品的最新内容。

        Returns:
            { competitor_id: [content_data, ...], ... }
        """
        competitors = self._monitor.list_competitors(user_id)
        results: dict[str, list[dict]] = {}

        for comp in competitors:
            try:
                results[comp["id"]] = await self.scrape_competitor(comp)
            except Exception as e:
                logger.error(f"竞品 {comp.get('account_name', '')} 爬取异常: {e}")
                results[comp["id"]] = []

        total = sum(len(v) for v in results.values())
        logger.info(f"全部竞品爬取完成", user_id=user_id, total_new=total)
        return results

    # ------------------------------------------------------------------
    # 内部提取逻辑
    # ------------------------------------------------------------------

    async def _extract_post(self, post: Any, platform: str, strategy: dict) -> dict:
        """从单个帖子 DOM 提取结构化数据。"""
        title = ""
        try:
            title_el = await post.query_selector(strategy["title_selector"])
            if title_el:
                title = (await title_el.inner_text()).strip()
        except Exception:
            pass

        if not title:
            return {}

        # 提取互动指标
        metrics: dict[str, int] = {"views": 0, "likes": 0, "comments": 0, "shares": 0}
        for metric_name, selector in strategy.get("metrics_selectors", {}).items():
            try:
                el = await post.query_selector(selector)
                if el:
                    text = (await el.inner_text()).strip()
                    metrics[metric_name] = self._parse_number(text)
            except Exception:
                pass

        return {
            "content_id": f"{platform}_{datetime.now(timezone.utc).timestamp()}_{hash(title) & 0xFFFFFFFF}",
            "title": title[:200],
            "content_type": "视频" if platform in ("抖音", "B站", "YouTube", "快手") else "图文",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "topics": [],
            "style_tags": [],
            "summary": title[:100],
        }

    @staticmethod
    def _parse_number(text: str) -> int:
        """解析数字文本：'1.2万' → 12000, '3.4k' → 3400"""
        import re

        text = text.replace(",", "").strip().lower()
        match = re.search(r"([\d.]+)\s*(万|w|k|亿)?", text)
        if not match:
            return 0
        num = float(match.group(1))
        unit = match.group(2)
        if unit in ("万", "w"):
            num *= 10000
        elif unit == "k":
            num *= 1000
        elif unit == "亿":
            num *= 100_000_000
        return int(num)
