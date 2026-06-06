import json

SYSTEM_BASE = "你是智媒圈AI助手，专业的自媒体内容创作专家。请用中文回复。"


class Prompts:
    @staticmethod
    def generate_content(
        topic: str,
        platform: str,
        persona: str,
        duration: int,
        rules: dict | None = None,
    ) -> tuple[str, str]:
        system = f"""{SYSTEM_BASE}
你擅长为不同平台创作口播内容。
平台特点：
- 抖音：节奏快，前3秒必须有钩子，时长短
- 小红书：干货+情绪，标题要有数字
- B站：深度内容，可以长视频
- 公众号：深度长文，逻辑清晰
- YouTube：国际化视角，SEO友好
- TikTok：全球化，趋势敏感"""

        if rules:
            rules_text = json.dumps(rules, ensure_ascii=False, indent=2)
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
        system = f"""{SYSTEM_BASE}
你擅长创作爆款标题。好标题的特点：
- 有数字（3个、5招、99%）
- 有悬念或反常识
- 有情绪共鸣
- 符合平台算法偏好"""

        if rules:
            rules_text = json.dumps(rules, ensure_ascii=False, indent=2)
            system += f"\n\n当前{platform}平台爆款规则（实时更新）：\n{rules_text}"

        prompt = f"""为以下主题生成{count}个爆款标题：

主题：{topic}
平台：{platform}

请按以下格式输出（JSON）：
{{
  "titles": [
    {{"title": "标题", "score": 95, "reason": "评分理由", "hook_type": "钩子类型"}}
  ]
}}

钩子类型包括：数字型、反常识型、痛点型、利益型、悬念型、对比型"""
        return system, prompt

    @staticmethod
    def score_content(
        title: str, body: str, platform: str, rules: dict | None = None
    ) -> tuple[str, str]:
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

        if rules:
            rules_text = json.dumps(rules, ensure_ascii=False, indent=2)
            system += f"\n\n当前{platform}平台爆款规则（实时更新）：\n{rules_text}"

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
