"""爆款规则分析引擎 - 从热门内容中提取爆款规律"""

import json
import re
from collections import Counter
from datetime import datetime
from typing import Any

from services.deepseek import DeepSeekClient
from services.prompts import SYSTEM_BASE


class RuleAnalyzer:
    """分析热门内容，提取爆款规则"""

    # 标题钩子类型分类
    HOOK_PATTERNS = {
        "数字型": r"\d+",
        "反常识型": r"(竟然|没想到|原来|居然|真的|不为人知)",
        "痛点型": r"(怎么办|如何|怎么|为什么|解决|摆脱)",
        "利益型": r"(赚钱|省钱|涨粉|爆款|流量|变现)",
        "悬念型": r"(真相|秘密|内幕|揭秘|曝光|揭露)",
        "对比型": r"(vs|对比|区别|不同|差距|PK)",
        "情绪型": r"(气死|震惊|无语|绝了|离谱|炸裂)",
        "权威型": r"(专家|大V|官方|认证|专业|资深)",
    }

    # 平台算法权重 - 覆盖全部 13 个平台
    PLATFORM_RULES: dict[str, dict[str, Any]] = {
        "抖音": {
            "title_max_len": 30,
            "hook_time": 3,
            "key_factors": ["完播率", "互动率", "分享率"],
            "content_type": "短视频",
            "category": "短视频",
            "best_duration": [15, 30, 60],
            "core_metric": "完播率",
            "cold_start_hours": "1-3",
            "qualification": "完播率>45%, 点赞率>3%, 评论率>0.5%",
        },
        "小红书": {
            "title_max_len": 20,
            "hook_time": 3,
            "key_factors": ["收藏率", "点赞率", "评论率"],
            "content_type": "图文/视频",
            "category": "种草",
            "best_duration": [60, 180, 300],
            "core_metric": "收藏率",
            "cold_start_hours": "2-6",
            "qualification": "CTR>12%, 收藏率>5%",
        },
        "B站": {
            "title_max_len": 40,
            "hook_time": 5,
            "key_factors": ["播放量", "弹幕数", "投币数"],
            "content_type": "中长视频",
            "category": "中长视频",
            "best_duration": [300, 600, 900],
            "core_metric": "播放量",
            "cold_start_hours": "6-24",
            "qualification": "CTR>8%, 投币率>2%",
        },
        "微博": {
            "title_max_len": 40,
            "hook_time": 0,
            "key_factors": ["转发量", "评论量", "点赞量"],
            "content_type": "图文",
            "category": "社交",
            "best_duration": [],
            "core_metric": "转发量",
            "cold_start_hours": "0.5-2",
            "qualification": "互动率>2%",
        },
        "知乎": {
            "title_max_len": 50,
            "hook_time": 0,
            "key_factors": ["赞同数", "收藏数", "评论数"],
            "content_type": "问答",
            "category": "问答",
            "best_duration": [],
            "core_metric": "赞同数",
            "cold_start_hours": "24-72",
            "qualification": "收藏/赞比>0.8",
        },
        "头条": {
            "title_max_len": 30,
            "hook_time": 0,
            "key_factors": ["阅读完成率", "CTR", "评论数"],
            "content_type": "资讯",
            "category": "资讯",
            "best_duration": [],
            "core_metric": "阅读完成率",
            "cold_start_hours": "1-4",
            "qualification": "CTR>5%, 完成率>30%",
        },
        "快手": {
            "title_max_len": 20,
            "hook_time": 3,
            "key_factors": ["完播率", "点赞率", "关注率"],
            "content_type": "短视频",
            "category": "短视频",
            "best_duration": [15, 30, 60],
            "core_metric": "完播率",
            "cold_start_hours": "1-2",
            "qualification": "完播率>35%",
        },
        "YouTube": {
            "title_max_len": 100,
            "hook_time": 5,
            "key_factors": ["CTR", "观看时长", "订阅转化"],
            "content_type": "视频",
            "category": "中长视频",
            "best_duration": [600, 900, 1200],
            "core_metric": "观看时长",
            "cold_start_hours": "6-24",
            "qualification": "CTR>5%, 平均观看>40%",
        },
        "TikTok": {
            "title_max_len": 30,
            "hook_time": 2,
            "key_factors": ["完播率", "分享率", "关注率"],
            "content_type": "短视频",
            "category": "短视频",
            "best_duration": [15, 30, 60],
            "core_metric": "完播率",
            "cold_start_hours": "0.5-2",
            "qualification": "3秒完播>60%, 分享率>1%",
        },
        "公众号": {
            "title_max_len": 64,
            "hook_time": 0,
            "key_factors": ["打开率", "分享率", "在看数"],
            "content_type": "图文",
            "category": "图文",
            "best_duration": [],
            "core_metric": "打开率",
            "cold_start_hours": "12-48",
            "qualification": "打开率>5%",
        },
        "视频号": {
            "title_max_len": 30,
            "hook_time": 3,
            "key_factors": ["社交传播", "完播率", "点赞率"],
            "content_type": "短视频",
            "category": "短视频",
            "best_duration": [30, 60],
            "core_metric": "社交传播深度",
            "cold_start_hours": "4-12",
            "qualification": "好友分享率>2%",
        },
        "百度热搜": {
            "title_max_len": 40,
            "hook_time": 0,
            "key_factors": ["搜索热度", "CTR", "停留时长"],
            "content_type": "资讯",
            "category": "资讯",
            "best_duration": [],
            "core_metric": "搜索热度",
            "cold_start_hours": "1-6",
            "qualification": "关键词匹配>70%",
        },
        "Instagram": {
            "title_max_len": 100,
            "hook_time": 2,
            "key_factors": ["Engagement Rate", "Saves", "Shares"],
            "content_type": "社交",
            "category": "社交",
            "best_duration": [15, 30, 60],
            "core_metric": "互动率",
            "cold_start_hours": "1-4",
            "qualification": "Engagement>3%",
        },
    }

    # 各平台最佳发布时间
    
BEST_POSTING_TIMES: dict[str, list[dict]] = {
    "抖音": [{"time": "12:00-13:00", "score": 85, "reason": "午休刷屏高峰"}, {"time": "18:00-20:00", "score": 95, "reason": "下班黄金档"}, {"time": "21:00-23:00", "score": 90, "reason": "睡前沉浸时段"}],
    "小红书": [{"time": "07:00-09:00", "score": 80, "reason": "早间种草"}, {"time": "12:00-14:00", "score": 85, "reason": "午休浏览"}, {"time": "20:00-22:00", "score": 90, "reason": "晚间高峰"}],
    "B站": [{"time": "12:00-14:00", "score": 80, "reason": "午休浏览"}, {"time": "18:00-20:00", "score": 85, "reason": "放学/下班"}, {"time": "20:00-23:00", "score": 95, "reason": "晚间黄金档"}],
    "微博": [{"time": "08:00-09:00", "score": 85, "reason": "早高峰刷屏"}, {"time": "12:00-14:00", "score": 80, "reason": "午休热点"}, {"time": "18:00-22:00", "score": 90, "reason": "晚间热搜"}],
    "知乎": [{"time": "08:00-09:00", "score": 75, "reason": "早间浏览"}, {"time": "12:00-14:00", "score": 80, "reason": "午休阅读"}, {"time": "20:00-22:00", "score": 90, "reason": "晚间深度阅读"}],
    "头条": [{"time": "07:00-08:00", "score": 85, "reason": "早间资讯"}, {"time": "12:00-13:00", "score": 80, "reason": "午休刷资讯"}, {"time": "18:00-20:00", "score": 90, "reason": "晚间资讯高峰"}],
    "快手": [{"time": "11:30-13:30", "score": 85, "reason": "午间休息"}, {"time": "19:00-22:00", "score": 90, "reason": "晚间活跃高峰"}],
    "YouTube": [{"time": "14:00-16:00", "score": 85, "reason": "提前发布抓索引"}, {"time": "09:00-11:00", "score": 80, "reason": "周末上午"}],
    "TikTok": [{"time": "18:00-21:00", "score": 90, "reason": "目标时区晚间"}, {"time": "12:00-15:00", "score": 80, "reason": "午休浏览"}],
    "公众号": [{"time": "07:00-08:30", "score": 90, "reason": "上班路上"}, {"time": "11:30-13:00", "score": 80, "reason": "午休浏览"}, {"time": "18:00-20:00", "score": 85, "reason": "下班通勤"}],
    "视频号": [{"time": "07:00-09:00", "score": 85, "reason": "早间社交"}, {"time": "12:00-13:00", "score": 80, "reason": "午休转发"}, {"time": "18:00-20:00", "score": 90, "reason": "晚间社交链"}],
    "百度热搜": [{"time": "08:00-10:00", "score": 85, "reason": "早间搜索高峰"}, {"time": "19:00-21:00", "score": 80, "reason": "晚间搜索"}],
    "Instagram": [{"time": "11:00-13:00", "score": 85, "reason": "午休浏览"}, {"time": "19:00-21:00", "score": 90, "reason": "晚间视觉消费"}],
}


class RuleAnalyzer:
    """爆款规则分析器"""

    PLATFORM_RULES = {
        "抖音": {"title_max_len": 30, "hook_time": 3, "key_factors": ["完播率", "点赞率", "评论率", "转发率"], "content_type": "短视频", "category": "短视频", "best_duration": [15, 30, 60], "core_metric": "完播率", "cold_start_hours": "1-3", "qualification": "完播率>45%"},
        "小红书": {"title_max_len": 20, "hook_time": 1, "key_factors": ["收藏率", "点击率", "评论率"], "content_type": "图文", "category": "种草", "best_duration": [30, 60, 180], "core_metric": "收藏率", "cold_start_hours": "2-6", "qualification": "收藏率>3%"},
        "B站": {"title_max_len": 30, "hook_time": 30, "key_factors": ["三连率", "弹幕密度", "完播率", "投币率"], "content_type": "中长视频", "category": "中长视频", "best_duration": [300, 600, 1200], "core_metric": "三连率", "cold_start_hours": "6-24", "qualification": "三连率>8%"},
        "微博": {"title_max_len": 100, "hook_time": 1, "key_factors": ["转发率", "热搜", "互动率"], "content_type": "社交", "category": "社交", "best_duration": [15, 30, 60], "core_metric": "转发量", "cold_start_hours": "0.5-2", "qualification": "转发率>1%"},
        "知乎": {"title_max_len": 50, "hook_time": 10, "key_factors": ["赞同率", "长尾流量", "专业度"], "content_type": "问答", "category": "问答", "best_duration": [120, 300, 600], "core_metric": "赞同数", "cold_start_hours": "24-72", "qualification": "赞同率>5%"},
        "头条": {"title_max_len": 28, "hook_time": 3, "key_factors": ["阅读完成率", "评论率", "转发率"], "content_type": "资讯", "category": "资讯", "best_duration": [30, 60, 120], "core_metric": "阅读完成率", "cold_start_hours": "1-4", "qualification": "阅读完成率>50%"},
        "快手": {"title_max_len": 30, "hook_time": 3, "key_factors": ["互动率", "完播率", "直播转化"], "content_type": "短视频", "category": "短视频", "best_duration": [15, 30, 60], "core_metric": "完播率", "cold_start_hours": "1-2", "qualification": "完播率>35%"},
        "YouTube": {"title_max_len": 70, "hook_time": 60, "key_factors": ["观看时长", "订阅转化", "完播率"], "content_type": "中长视频", "category": "中长视频", "best_duration": [600, 1200, 2400], "core_metric": "观看时长", "cold_start_hours": "6-24", "qualification": "观看时长>40%"},
        "TikTok": {"title_max_len": 100, "hook_time": 2, "key_factors": ["完播率", "趋势跟随", "音乐卡点"], "content_type": "短视频", "category": "短视频", "best_duration": [15, 30, 60], "core_metric": "完播率", "cold_start_hours": "0.5-2", "qualification": "完播率>40%"},
        "公众号": {"title_max_len": 30, "hook_time": 5, "key_factors": ["打开率", "转发率", "阅读完成率"], "content_type": "图文", "category": "图文", "best_duration": [120, 300, 600], "core_metric": "打开率", "cold_start_hours": "12-48", "qualification": "打开率>3%"},
        "视频号": {"title_max_len": 30, "hook_time": 3, "key_factors": ["转发率", "社交传播", "完播率"], "content_type": "短视频", "category": "短视频", "best_duration": [15, 30, 60], "core_metric": "社交传播", "cold_start_hours": "4-12", "qualification": "转发率>1%"},
        "百度热搜": {"title_max_len": 30, "hook_time": 1, "key_factors": ["搜索热度", "点击率"], "content_type": "资讯", "category": "资讯", "best_duration": [15, 30, 60], "core_metric": "搜索热度", "cold_start_hours": "1-6", "qualification": "关键词匹配>70%"},
        "Instagram": {"title_max_len": 100, "hook_time": 2, "key_factors": ["互动率", "收藏", "分享"], "content_type": "社交", "category": "社交", "best_duration": [15, 30, 60], "core_metric": "互动率", "cold_start_hours": "1-4", "qualification": "互动率>3%"},
    }

    @staticmethod
    def analyze(platform: str, rules: dict | None = None) -> dict:
        if not rules:
            return {"error": "no_rules", "platform": platform}
        return {"platform": platform, "title_rules": rules.get("title_rules", []), "hook_patterns": rules.get("hook_patterns", []), "trending_topics": rules.get("trending_topics", [])[:10], "best_practices": rules.get("best_practices", []), "algorithm": rules.get("algorithm", {})}

    @staticmethod
    def get_trending_topics(platform: str, titles: list[str] | None = None) -> list[dict]:
        """获取平台热门话题。

        当提供实时采集的标题列表时，通过 jieba 分词实时提取；
        否则从静态 rules 文件读取（存量数据）。

        Args:
            platform: 平台名称
            titles: 可选，实时采集到的标题列表。为空时从 rules 文件读取。

        Returns:
            热门话题列表，每个话题含 topic/source 字段
        """
        from pathlib import Path

        # 有实时数据：分词提取
        if titles:
            try:
                from monitors.parser import HotContentParser
                topics = HotContentParser.extract_topics(titles)
                return [{"topic": t, "source": "live", "platform": platform} for t in topics]
            except Exception:
                pass

        # 无实时数据：从静态 rules 文件读取
        rules_path = (
            Path(__file__).resolve().parent.parent.parent
            / "data" / "rules" / f"{platform}.json"
        )
        if rules_path.exists():
            try:
                with open(rules_path, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                trending = rules.get("trending_topics", [])
                result = []
                for t in trending:
                    if isinstance(t, str):
                        result.append({"topic": t, "source": "cached", "platform": platform})
                    elif isinstance(t, dict):
                        result.append({
                            "topic": t.get("topic", t.get("title", "")),
                            "source": t.get("source", "cached"),
                            "platform": platform,
                        })
                return result
            except Exception:
                pass

        return []

    @staticmethod
    def get_title_suggestions(platform: str, topic: str) -> list[dict]:
        """基于平台规则生成标题建议。

        Args:
            platform: 平台名称
            topic: 话题/主题

        Returns:
            标题建议列表，每个包含 title/hook_type/template
        """
        from pathlib import Path

        # 尝试从规则文件读取标题规则作为模板
        rules_path = (
            Path(__file__).resolve().parent.parent.parent
            / "data" / "rules" / f"{platform}.json"
        )
        suggestions = []

        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                rules = json.load(f)
            title_rules = rules.get("title_rules", [])
            for rule in title_rules[:5]:
                formula = rule.get("formula", "")
                suggestions.append({
                    "title": f"「{topic}」{formula}",
                    "hook_type": rule.get("type", ""),
                    "ctr_rating": rule.get("ctr_rating", ""),
                    "template": formula,
                })
        except Exception:
            pass

        # 无规则文件时使用默认模板
        if not suggestions:
            defaults = [
                {"title": f"3个{topic}方法，最后一个太绝了", "hook_type": "数字型", "ctr_rating": "★★★★☆"},
                {"title": f"为什么{topic}很重要？看完你就懂了", "hook_type": "悬念型", "ctr_rating": "★★★★☆"},
                {"title": f"你是不是也遇到了{topic}的困扰？", "hook_type": "痛点型", "ctr_rating": "★★★★☆"},
                {"title": f"没人告诉你{topic}的真相", "hook_type": "反常识型", "ctr_rating": "★★★★★"},
                {"title": f"学会{topic}，我的人生变了", "hook_type": "利益型", "ctr_rating": "★★★★☆"},
            ]
            suggestions = defaults

        return suggestions

    @staticmethod
    def get_best_posting_time(platform: str) -> dict:
        time_slots = RuleAnalyzer.BEST_POSTING_TIMES.get(platform, [])
        if not time_slots:
            return {"platform": platform, "time_slots": [], "recommendation": f"暂无{platform}的数据"}
        best = max(time_slots, key=lambda x: x["score"])
        return {"platform": platform, "time_slots": time_slots, "recommendation": f"推荐在{best['time']}发布，{best['reason']}"}

    @staticmethod
    def merge_rules(ai_rules: dict, title_analysis: dict, existing_rules: dict | None = None) -> dict:
        merged = {"title_rules": ai_rules.get("title_rules") or title_analysis.get("title_rules") or (existing_rules or {}).get("title_rules", []), "hook_patterns": ai_rules.get("hook_patterns") or title_analysis.get("hook_patterns") or (existing_rules or {}).get("hook_patterns", []), "trending_topics": ai_rules.get("trending_topics") or title_analysis.get("trending_topics") or (existing_rules or {}).get("trending_topics", []), "best_practices": ai_rules.get("best_practices") or title_analysis.get("best_practices") or (existing_rules or {}).get("best_practices", []), "algorithm": ai_rules.get("algorithm") or title_analysis.get("algorithm") or (existing_rules or {}).get("algorithm", {})}
        return merged
