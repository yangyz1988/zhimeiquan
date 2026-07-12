"""趋势热词聚合服务 — 修复 trending_topics 空列表问题

跨平台热词聚合：
1. 聚合各平台 ScrapeResult.titles
2. jieba 分词 + TF 统计 提取高频热词
3. 写入 data/rules/{platform}.json 的 trending_topics 字段
4. 跨平台热点发现 — 同一话题出现在多个平台 → 标记为跨平台爆款

典型用法:
    svc = HotspotService(rules_dir="../data/rules")
    svc.refresh_trending_topics("抖音", titles)
    cross = svc.get_cross_platform_hotspots()
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.logging import logger


class HotspotService:
    """趋势热词聚合 + 跨平台热点发现。

    不依赖单个平台的 trending_topics，而是：
    1. 聚合所有平台 ScrapeResult.titles
    2. jieba 分词 + TF 提取高频热词
    3. 写入 data/rules/{platform}.json 的 trending_topics 字段
    """

    def __init__(self, rules_dir: str = "../data/rules"):
        self._rules_dir = Path(rules_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh_trending_topics(
        self, platform: str, titles: list[str], save: bool = True
    ) -> list[str]:
        """用新采集到的标题文本更新平台的 trending_topics。

        Args:
            platform: 平台名称
            titles: 实时采集到的标题列表
            save: 是否保存到 rules 文件（默认 True）

        Returns:
            提取的热门话题列表
        """
        if not titles:
            return []

        from monitors.parser import HotContentParser
        topics = HotContentParser.extract_topics(titles, top_n=25)

        if save and topics:
            self._update_rules_file(platform, topics)

        logger.info(f"trending_topics 已刷新", platform=platform, topics=len(topics))
        return topics

    def refresh_all_platforms(
        self, platform_titles: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        """批量刷新所有平台的 trending_topics。

        Args:
            platform_titles: {"抖音": [title1, ...], "B站": [title2, ...], ...}

        Returns:
            {platform: [topic1, ...], ...}
        """
        results = {}
        for platform, titles in platform_titles.items():
            results[platform] = self.refresh_trending_topics(platform, titles)
        return results

    def get_cross_platform_hotspots(
        self, min_platforms: int = 2
    ) -> list[dict]:
        """跨平台热点发现 — 同一话题出现在多个平台 → 标记为跨平台爆款。

        扫描所有 rules 文件的 trending_topics 字段，
        找出在多个平台同时出现的热门话题。

        Args:
            min_platforms: 最少出现在几个平台才视为跨平台（默认 2）

        Returns:
            [
                {
                    "topic": "AI 工具",
                    "platforms": ["抖音", "小红书", "B站"],
                    "platform_count": 3,
                    "score": 30,
                },
                ...
            ]
        """
        topic_platforms: dict[str, set[str]] = {}

        for filepath in sorted(self._rules_dir.glob("*.json")):
            if filepath.name.startswith("_"):
                continue
            platform = filepath.stem
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                trending = rules.get("trending_topics", [])
                for t in trending:
                    if isinstance(t, str):
                        key = t.strip()
                    elif isinstance(t, dict):
                        key = (t.get("topic") or t.get("title") or "").strip()
                    else:
                        continue
                    if key:
                        if key not in topic_platforms:
                            topic_platforms[key] = set()
                        topic_platforms[key].add(platform)
            except Exception:
                continue

        cross = []
        for topic, platforms in topic_platforms.items():
            if len(platforms) >= min_platforms:
                cross.append({
                    "topic": topic,
                    "platforms": sorted(platforms),
                    "platform_count": len(platforms),
                    "score": len(platforms) * 10,
                })

        cross.sort(key=lambda x: -x["score"])
        return cross

    def get_trending_summary(self) -> dict:
        """获取全平台趋势摘要。

        Returns:
            {
                "total_platforms": int,
                "total_unique_topics": int,
                "cross_platform_hotspots": [...],
                "platform_topics": { "抖音": [...], ... },
                "generated_at": "2026-07-04T...",
            }
        """
        platform_topics: dict[str, list[str]] = {}
        all_topics: set[str] = set()

        for filepath in sorted(self._rules_dir.glob("*.json")):
            if filepath.name.startswith("_"):
                continue
            platform = filepath.stem
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                trending = rules.get("trending_topics", [])
                topics = []
                for t in trending:
                    if isinstance(t, str):
                        topic = t.strip()
                    elif isinstance(t, dict):
                        topic = (t.get("topic") or t.get("title") or "").strip()
                    else:
                        continue
                    if topic:
                        topics.append(topic)
                        all_topics.add(topic)
                platform_topics[platform] = topics
            except Exception:
                platform_topics[platform] = []

        cross = self.get_cross_platform_hotspots()

        return {
            "total_platforms": len(platform_topics),
            "total_unique_topics": len(all_topics),
            "cross_platform_hotspots": cross[:20],
            "platform_topics": {
                p: t[:10] for p, t in platform_topics.items()
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _update_rules_file(self, platform: str, topics: list[str]):
        """将提取的热门话题写入平台规则文件的 trending_topics 字段。"""
        filepath = self._rules_dir / f"{platform}.json"

        rules: dict[str, Any] = {}
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    rules = json.load(f)
            except (json.JSONDecodeError, OSError):
                rules = {}

        # 保留原有元数据，只更新 trending_topics
        rules["trending_topics"] = topics
        rules["trending_topics_updated_at"] = datetime.now(timezone.utc).isoformat()

        # 确保基本字段存在
        rules.setdefault("platform", platform)
        rules.setdefault("last_updated", datetime.now(timezone.utc).isoformat())

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.warning(f"保存 trending_topics 到 {filepath.name} 失败: {e}")
