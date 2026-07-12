import json
from pathlib import Path

from .content_loader import get_methodology, get_persona, get_template

SYSTEM_BASE = "你是智媒圈AI助手，专业的自媒体内容创作专家。请用中文回复。"

# 平台规则目录（动态注入）
RULES_DIR = Path(__file__).resolve().parents[2] / "data" / "rules"


def _load_platform_rules(platform: str) -> dict | None:
    """从 data/rules/{platform}.json 加载平台规则。"""
    filepath = RULES_DIR / f"{platform}.json"
    if not filepath.exists():
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _get_platform_traits(platform: str, rules: dict | None = None) -> str:
    """根据平台规则动态生成平台特点描述。"""
    if rules:
        # 从规则文件提取核心信息
        algo = rules.get("algorithm", {})
        core_metric = algo.get("core_metric", "互动率")
        cold_start = algo.get("cold_start_window_hours", "未知")
        title_rules = rules.get("title_rules", [])
        hook_patterns = rules.get("hook_patterns", [])

        traits = f"- 核心指标：{core_metric}\n"
        traits += f"- 冷启动窗口：{cold_start}\n"
        if title_rules:
            top_rules = title_rules[:3]
            traits += "- 高效标题模式：" + "、".join(r.get("type", r.get("rule", "")) for r in top_rules) + "\n"
        if hook_patterns:
            top_hooks = hook_patterns[:3]
            traits += "- 热门钩子：" + "、".join(h.get("type", h.get("pattern", "")) for h in top_hooks) + "\n"
        return traits

    # fallback：硬编码的基本特点（仅当规则文件不存在时使用）
    fallback_traits = {
        "抖音": "- 节奏快，前3秒必须有钩子，完播率是核心\n",
        "小红书": "- 干货+情绪，标题要有数字，收藏率权重高\n",
        "B站": "- 深度内容，弹幕互动，三连率是关键\n",
        "快手": "- 接地气，老铁文化，完播率+互动率\n",
        "微博": "- 热点蹭热搜，转发量核心，140字配图\n",
        "知乎": "- 深度问答，收藏/赞比，长文结构化\n",
        "头条": "- 阅读完成率核心，CTR驱动，信息密度\n",
        "公众号": "- 打开率核心，深度长文，固定推送时间\n",
        "视频号": "- 社交裂变核心，转发率>完播率\n",
        "百度热搜": "- 搜索热度匹配，关键词布局\n",
        "YouTube": "- 国际化视角，SEO友好，观看时长核心\n",
        "TikTok": "- 全球化，趋势敏感，前2秒定成败\n",
        "Instagram": "- 视觉消费，互动率核心，Stories+Reels\n",
    }
    return fallback_traits.get(platform, "- 通用平台规则\n")


class Prompts:
    @staticmethod
    def generate_content(
        topic: str,
        platform: str,
        persona: str,
        duration: int,
        rules: dict | None = None,
    ) -> tuple[str, str]:
        # 动态加载平台规则
        if rules is None:
            rules = _load_platform_rules(platform)

        platform_traits = _get_platform_traits(platform, rules)

        system = f"""{SYSTEM_BASE}
你擅长为不同平台创作口播内容。

## {platform} 平台特点（来自实时规则库）
{platform_traits}"""

        template = get_template(platform)
        if template:
            system += f"\n\n## {platform} 平台爆款模板（来自知识库）\n{template}"

        persona_doc = get_persona(persona)
        if persona_doc:
            system += f"\n\n## {persona} 人设指南（来自知识库）\n{persona_doc}"

        hook_doc = get_methodology("hook")
        if hook_doc:
            system += f"\n\n## 钩子力方法论（Fire Score 维度 1 · 权重 25%）\n{hook_doc}"

        if rules:
            # 只注入关键字段，避免 prompt 过长
            compact_rules = {
                "title_rules": rules.get("title_rules", [])[:5],
                "hook_patterns": rules.get("hook_patterns", [])[:5],
                "algorithm": rules.get("algorithm", {}),
                "trending_topics": rules.get("trending_topics", [])[:10],
            }
            rules_text = json.dumps(compact_rules, ensure_ascii=False, indent=2)
            system += f"\n\n当前{platform}平台爆款规则（实时更新）：\n{rules_text}"

        prompt = f"""请为以下主题生成口播内容：

主题：{platform} - {topic}
人设：{persona}
目标时长：{duration}秒

请按以下格式输出（JSON）：
{{
  "titles": ["标题1", "标题2", "标题3", "标题4", "标题5"],
  "script": "完整口播稿，包含[开场][正文][结尾]标记",
  "subtitles": [{{"time": "00:00", "text": "字幕内容"}}],
  "tags": ["标签1", "标签2", "标签3"],
  "hook": "前3秒钩子文案",
  "call_to_action": "结尾引导语"
}}"""
        return system, prompt

    @staticmethod
    def generate_titles(
        topic: str, platform: str, count: int = 5, rules: dict | None = None
    ) -> tuple[str, str]:
        # 动态加载平台规则
        if rules is None:
            rules = _load_platform_rules(platform)

        platform_traits = _get_platform_traits(platform, rules)

        system = f"""{SYSTEM_BASE}
你擅长创作爆款标题。

## {platform} 平台标题特点
{platform_traits}

好标题的特点：
- 有数字（3个、5招、99%）
- 有悬念或反常识
- 有情绪共鸣
- 符合平台算法偏好"""

        template = get_template(platform)
        if template:
            system += f"\n\n## {platform} 平台爆款模板（来自知识库）\n{template}"

        hook_doc = get_methodology("hook")
        if hook_doc:
            system += f"\n\n## 钩子力方法论（Fire Score 维度 1 · 权重 25%）\n{hook_doc}"

        if rules:
            compact_rules = {
                "title_rules": rules.get("title_rules", [])[:5],
                "hook_patterns": rules.get("hook_patterns", [])[:5],
            }
            rules_text = json.dumps(compact_rules, ensure_ascii=False, indent=2)
            system += f"\n\n当前{platform}平台爆款规则（实时更新）：\n{rules_text}"

        prompt = f"""为以下主题生成{count}个爆款标题：

主题：{topic}
平台：{platform}

请按以下格式输出（JSON）：
{{
  "titles": [
    {{ "title": "标题", "score": 95, "reason": "评分理由", "hook_type": "钩子类型" }}
  ]
}}

钩子类型包括：数字型、反常识型、痛点型、利益型、悬念型、对比型"""
        return system, prompt

    @staticmethod
    def score_content(
        title: str, body: str, platform: str, rules: dict | None = None
    ) -> tuple[str, str]:
        # 动态加载平台规则
        if rules is None:
            rules = _load_platform_rules(platform)

        system = f"""{SYSTEM_BASE}
你是Fire Score评分专家，从5个维度评估内容质量：
1. 钩子力(25%)：前3秒能否让人停住
2. 信任度(20%)：内容是否可信、有依据
3. 完播力(20%)：节奏是否紧凑、不无聊
4. 转化力(20%)：用户看完会不会关注/收藏
5. 情绪值(15%)：有没有情绪共鸣

爆款等级：
- Lv1 必爆：90分以上
- Lv2 稳爆：80-89分
- Lv3 高爆：70-79分
- Lv4 普爆：60-69分
- Lv5 基础：60分以下"""

        for dim in ("hook", "trust", "retention", "conversion", "emotion"):
            doc = get_methodology(dim)
            if doc:
                system += f"\n\n## Fire Score · {dim} 维度评分标准（来自知识库）\n{doc}"

        if rules:
            algo = rules.get("algorithm", {})
            if algo:
                system += f"\n\n## {platform} 平台算法参数\n{json.dumps(algo, ensure_ascii=False, indent=2)}"

        prompt = f"""请对以下内容进行Fire Score评分：

平台：{platform}
标题：{title}
正文：{body}

请按以下格式输出（JSON）：
{{
  "hook": 85,
  "trust": 78,
  "retention": 82,
  "conversion": 76,
  "emotion": 80,
  "total": 80,
  "level": "Lv2 稳爆",
  "suggestions": ["建议1", "建议2", "建议3"],
  "analysis": "综合分析"
}}"""
        return system, prompt