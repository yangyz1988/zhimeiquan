"""内容模板服务 - 可复用模板"""

import json
from pathlib import Path
from typing import Any

from services.logging import logger


class TemplateService:
    """内容模板服务"""

    def __init__(self, templates_dir: str = "../data/templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._init_default_templates()

    def _init_default_templates(self):
        """初始化默认模板"""
        default_templates = [
            {
                "id": "tutorial_basic",
                "name": "教程入门",
                "category": "教程",
                "platform": "通用",
                "structure": [
                    {
                        "section": "hook",
                        "duration": 3,
                        "template": "你以为{topic}很难？其实...",
                    },
                    {
                        "section": "problem",
                        "duration": 5,
                        "template": "很多人卡在{problem_point}",
                    },
                    {
                        "section": "solution",
                        "duration": 20,
                        "template": "其实只需要3步：\n1. {step1}\n2. {step2}\n3. {step3}",
                    },
                    {
                        "section": "proof",
                        "duration": 10,
                        "template": "我已经通过{result}",
                    },
                    {
                        "section": "cta",
                        "duration": 5,
                        "template": "关注我，下期分享{next_topic}",
                    },
                ],
            },
            {
                "id": "review_product",
                "name": "好物推荐",
                "category": "种草",
                "platform": "小红书",
                "structure": [
                    {
                        "section": "hook",
                        "duration": 3,
                        "template": "姐妹们！这个{product}真的绝了",
                    },
                    {
                        "section": "pain",
                        "duration": 5,
                        "template": "之前一直{old_problem}",
                    },
                    {
                        "section": "solution",
                        "duration": 15,
                        "template": "直到我发现了{product}",
                    },
                    {
                        "section": "benefits",
                        "duration": 15,
                        "template": "用了一周，{benefit1}、{benefit2}",
                    },
                    {
                        "section": "verdict",
                        "duration": 5,
                        "template": "真心推荐给{audience}",
                    },
                ],
            },
            {
                "id": "opinion_hot",
                "name": "观点输出",
                "category": "观点",
                "platform": "抖音",
                "structure": [
                    {
                        "section": "hook",
                        "duration": 3,
                        "template": "{controversial_opinion}，我为什么这么说",
                    },
                    {
                        "section": "argument",
                        "duration": 20,
                        "template": "首先...\n其次...\n最后...",
                    },
                    {
                        "section": "evidence",
                        "duration": 15,
                        "template": "我见过/做过{evidence}",
                    },
                    {
                        "section": "conclusion",
                        "duration": 10,
                        "template": "所以我的结论是{conclusion}",
                    },
                    {
                        "section": "discussion",
                        "duration": 5,
                        "template": "你怎么看？评论区聊聊",
                    },
                ],
            },
            {
                "id": "vlog_daily",
                "name": "日常Vlog",
                "category": "生活",
                "platform": "B站",
                "structure": [
                    {
                        "section": "hook",
                        "duration": 5,
                        "template": "今天带大家体验{activity}",
                    },
                    {
                        "section": "intro",
                        "duration": 10,
                        "template": "首先介绍一下背景...",
                    },
                    {"section": "process", "duration": 30, "template": "接下来我们..."},
                    {
                        "section": "highlight",
                        "duration": 10,
                        "template": "最精彩的部分来了...",
                    },
                    {
                        "section": "ending",
                        "duration": 5,
                        "template": "今天的分享就到这里",
                    },
                ],
            },
        ]

        for template in default_templates:
            filepath = self.templates_dir / f"{template['id']}.json"
            if not filepath.exists():
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(template, f, ensure_ascii=False, indent=2)

    def list_templates(
        self, category: str | None = None, platform: str | None = None
    ) -> list[dict]:
        """列出模板"""
        templates = []
        for f in self.templates_dir.glob("*.json"):
            with open(f, "r", encoding="utf-8") as file:
                template = json.load(file)
            if category and template.get("category") != category:
                continue
            if (
                platform
                and template.get("platform") != platform
                and template.get("platform") != "通用"
            ):
                continue
            templates.append(template)
        return templates

    def get_template(self, template_id: str) -> dict | None:
        """获取模板"""
        filepath = self.templates_dir / f"{template_id}.json"
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_template(self, template: dict) -> dict:
        """保存模板"""
        if "id" not in template:
            raise ValueError("模板必须包含 id")
        filepath = self.templates_dir / f"{template['id']}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        logger.info(f"模板已保存: {template['id']}")
        return template

    def apply_template(
        self, template_id: str, variables: dict[str, str]
    ) -> dict[str, str]:
        """应用模板，替换变量"""
        template = self.get_template(template_id)
        if not template:
            return {}

        result = {
            "template_id": template_id,
            "name": template["name"],
            "sections": [],
        }

        for section in template["structure"]:
            content = section["template"]
            for key, value in variables.items():
                content = content.replace(f"{{{key}}}", value)
            result["sections"].append(
                {
                    "section": section["section"],
                    "duration": section["duration"],
                    "content": content,
                }
            )

        return result
