"""内容洞察引擎 - 基于监控数据分析趋势、预测爆款"""

import json
import re
from pathlib import Path

from monitors.analyzer import RuleAnalyzer
from monitors.scraper import PlatformScraper
from services.logging import logger


class ContentInsightsEngine:
    """内容洞察引擎"""

    PLATFORM_BEST_TIMES: dict[str, list[dict]] = {
        "抖音": [
            {"time": "12:00-13:00", "score": 85, "reason": "午休高峰"},
            {"time": "18:00-20:00", "score": 95, "reason": "下班黄金档"},
            {"time": "21:00-23:00", "score": 90, "reason": "睡前刷屏"},
        ],
        "小红书": [
            {"time": "07:00-09:00", "score": 80, "reason": "早间种草"},
            {"time": "12:00-14:00", "score": 85, "reason": "午休浏览"},
            {"time": "20:00-22:00", "score": 90, "reason": "晚间高峰"},
        ],
        "B站": [
            {"time": "18:00-20:00", "score": 85, "reason": "放学/下班"},
            {"time": "20:00-23:00", "score": 95, "reason": "晚间黄金档"},
        ],
    }

    HOOK_TYPES = [
        "数字型", "反常识型", "痛点型", "利益型", "悬念型", "对比型", "情绪型", "权威型",
    ]

    def __init__(
        self,
        rules_dir: str = "../data/rules",
        analytics_dir: str = "../data/analytics",
    ):
        self.rules_dir = Path(rules_dir)
        self.analytics_dir = Path(analytics_dir)
        self.scraper = PlatformScraper()
        self.analyzer = RuleAnalyzer()

    def _load_platform_rules(self, platform: str) -> dict | None:
        filepath = self.rules_dir / f"{platform}.json"
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def analyze_trends(self, platform: str, days: int = 7) -> dict:
        rules = self._load_platform_rules(platform)
        if not rules:
            return {"platform": platform, "trends": [], "hot_topics": []}

        hook_patterns = rules.get("hook_patterns", [])
        trending = rules.get("trending_topics", [])
        title_rules = rules.get("title_rules", [])

        trends = []
        for hook in hook_patterns[:5]:
            trends.append({
                "type": "hook_pattern",
                "name": hook.get("type", "未知"),
                "count": hook.get("count", 0),
                "direction": "rising" if hook.get("count", 0) > 3 else "stable",
            })

        return {
            "platform": platform,
            "trends": trends,
            "hot_topics": trending[:10],
            "title_patterns": title_rules[:5],
            "summary": f"过去{days}天，{platform}平台共分析{len(hook_patterns)}种钩子模式",
        }

    def predict_viral_topic(self, platform: str) -> dict:
        rules = self._load_platform_rules(platform)
        if not rules:
            return {"platform": platform, "predictions": []}

        trending = rules.get("trending_topics", [])
        hook_patterns = rules.get("hook_patterns", [])

        predictions = []
        for topic in trending[:5]:
            score = min(95, 60 + len(hook_patterns) * 3)
            predictions.append({
                "topic": topic if isinstance(topic, str) else topic.get("title", ""),
                "viral_score": score,
                "reason": f"匹配{len(hook_patterns)}种爆款钩子模式",
                "suggested_hook": hook_patterns[0].get("type", "数字型") if hook_patterns else "数字型",
            })

        return {"platform": platform, "predictions": predictions}

    def get_content_recommendations(self, topic: str, platform: str) -> dict:
        rules = self._load_platform_rules(platform)
        if not rules:
            return {
                "topic": topic,
                "platform": platform,
                "hook_type": "数字型",
                "best_duration": 60,
                "title_templates": [],
            }

        hook_patterns = rules.get("hook_patterns", [])
        best_hook = hook_patterns[0].get("type", "数字型") if hook_patterns else "数字型"
        best_practices = rules.get("best_practices", [])

        return {
            "topic": topic,
            "platform": platform,
            "hook_type": best_hook,
            "best_duration": self.analyzer.PLATFORM_RULES.get(platform, {}).get("best_duration", 60),
            "title_templates": rules.get("title_rules", [])[:3],
            "best_practices": best_practices[:3],
        }

    def get_optimal_posting_time(self, platform: str) -> dict:
        time_slots = self.PLATFORM_BEST_TIMES.get(platform, [])
        if not time_slots:
            return {
                "platform": platform,
                "time_slots": [],
                "recommendation": f"暂无{platform}的最佳发布时机数据",
            }

        best = max(time_slots, key=lambda x: x["score"])
        return {
            "platform": platform,
            "time_slots": time_slots,
            "recommendation": f"推荐{platform}在{best['time']}发布，{best['reason']}",
        }
