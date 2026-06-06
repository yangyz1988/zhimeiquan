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

    # 平台算法权重
    PLATFORM_RULES = {
        "抖音": {
            "title_max_len": 30,
            "hook_time": 3,
            "key_factors": ["完播率", "互动率", "分享率"],
            "content_type": "短视频",
            "best_duration": [15, 30, 60],
        },
        "小红书": {
            "title_max_len": 20,
            "hook_time": 3,
            "key_factors": ["收藏率", "点赞率", "评论率"],
            "content_type": "图文/视频",
            "best_duration": [60, 180, 300],
        },
        "B站": {
            "title_max_len": 40,
            "hook_time": 5,
            "key_factors": ["播放量", "弹幕数", "投币数"],
            "content_type": "中长视频",
            "best_duration": [300, 600, 900],
        },
        "公众号": {
            "title_max_len": 64,
            "hook_time": 0,
            "key_factors": ["打开率", "分享率", "在看数"],
            "content_type": "图文",
            "best_duration": [],
        },
        "YouTube": {
            "title_max_len": 100,
            "hook_time": 5,
            "key_factors": ["CTR", "观看时长", "订阅转化"],
            "content_type": "视频",
            "best_duration": [600, 900, 1200],
        },
        "TikTok": {
            "title_max_len": 30,
            "hook_time": 2,
            "key_factors": ["完播率", "分享率", "关注率"],
            "content_type": "短视频",
            "best_duration": [15, 30, 60],
        },
    }

    def __init__(self):
        self.client = DeepSeekClient()

    def analyze_title_patterns(self, titles: list[dict]) -> dict[str, Any]:
        """分析标题钩子模式"""
        pattern_counts = Counter()
        hook_examples = {}

        for item in titles:
            title = item.get("title", "")
            for pattern_name, regex in self.HOOK_PATTERNS.items():
                if re.search(regex, title):
                    pattern_counts[pattern_name] += 1
                    if pattern_name not in hook_examples:
                        hook_examples[pattern_name] = []
                    if len(hook_examples[pattern_name]) < 3:
                        hook_examples[pattern_name].append(title)

        return {
            "total": len(titles),
            "patterns": dict(pattern_counts.most_common()),
            "examples": hook_examples,
            "hot_keywords": self._extract_hot_keywords(
                [t.get("title", "") for t in titles]
            ),
        }

    def _extract_hot_keywords(self, titles: list[str]) -> list[str]:
        """提取热门关键词"""
        word_counter = Counter()
        for title in titles:
            # 简单分词（实际应使用 jieba）
            words = re.findall(r"[\u4e00-\u9fa5]{2,}", title)
            word_counter.update(words)
        return [w for w, _ in word_counter.most_common(20)]

    async def generate_platform_rules(
        self, platform: str, hot_content: list[dict]
    ) -> dict[str, Any]:
        """用 AI 分析热门内容，生成平台爆款规则"""
        platform_config = self.PLATFORM_RULES.get(platform, {})

        # 构建分析 prompt
        titles_text = "\n".join(
            [
                f"- {item.get('title', '')} (热度: {item.get('heat', 0)})"
                for item in hot_content[:15]
            ]
        )

        prompt = f"""分析以下{platform}平台的热门内容，总结爆款规律：

热门内容：
{titles_text}

平台特点：
- 内容类型：{platform_config.get("content_type", "未知")}
- 标题最长：{platform_config.get("title_max_len", "未知")}字
- 关键指标：{", ".join(platform_config.get("key_factors", []))}

请输出 JSON 格式的爆款规则：
{{
  "title_rules": [
    {{"rule": "规则描述", "example": "示例标题", "importance": "高/中/低"}}
  ],
  "content_rules": [
    {{"rule": "规则描述", "reason": "原因"}}
  ],
  "hook_patterns": [
    {{"pattern": "钩子类型", "description": "描述", "examples": ["示例1", "示例2"]}}
  ],
  "trending_topics": ["热门话题1", "热门话题2"],
  "best_practices": ["最佳实践1", "最佳实践2"],
  "avoid_list": ["避坑事项1", "避坑事项2"],
  "score": {{
    "hook": 85,
    "trend": 90,
    "engagement": 80,
    "monetization": 75
  }}
}}"""

        try:
            system = f"""{SYSTEM_BASE}
你是{platform}平台的爆款内容分析专家，精通平台算法和用户行为。
你需要从热门内容中提炼出可复用的爆款规则。"""

            result = await self.client.chat(prompt, system=system)
            return json.loads(result)
        except Exception as e:
            print(f"[Analyzer] AI 分析失败: {e}")
            return self._get_default_rules(platform)

    def _get_default_rules(self, platform: str) -> dict:
        """获取默认规则模板"""
        return {
            "title_rules": [
                {"rule": "标题包含数字", "example": "3个技巧...", "importance": "高"},
                {
                    "rule": "制造悬念或好奇心",
                    "example": "没想到...",
                    "importance": "高",
                },
            ],
            "content_rules": [
                {"rule": "前3秒必须有钩子", "reason": "用户注意力短暂"},
            ],
            "hook_patterns": [
                {
                    "pattern": "数字型",
                    "description": "用数字吸引眼球",
                    "examples": ["3个技巧", "99%的人"],
                },
            ],
            "trending_topics": [],
            "best_practices": ["保持更新频率", "与粉丝互动"],
            "avoid_list": ["避免违规内容"],
            "score": {"hook": 70, "trend": 70, "engagement": 70, "monetization": 70},
        }

    def merge_rules(self, platform_rules: dict, title_analysis: dict) -> dict:
        """合并 AI 规则和统计分析"""
        return {
            **platform_rules,
            "title_analysis": title_analysis,
            "updated_at": datetime.now().isoformat(),
        }
