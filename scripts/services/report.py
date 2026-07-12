"""平台爆款规则分析报告 — 免费增长钩子

基于浏览器采集的实时数据和静态规则库，生成面向公开传播的
"XX平台爆款规则分析报告"，吸引自媒体创作者注册。

可用作：
- 独立落地页（SEO 关键词：抖音爆款规则、小红书算法揭秘）
- 邮件订阅钩子（输入邮箱获取完整报告）
- 社交媒体内容素材（每期报告 = 一篇爆款内容）
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.logging import logger


class ReportGenerator:
    """规则分析报告生成器。

    从 data/rules/ 读取最新规则数据，生成人类可读的 Markdown 报告。
    """

    def __init__(self, rules_dir: str = "../data/rules"):
        self._rules_dir = Path(rules_dir)

    def generate_platform_report(self, platform: str) -> dict:
        """生成单平台爆款规则报告。

        Returns:
            {
                "platform": "抖音",
                "title": "抖音爆款规则分析报告",
                "summary": "一句话摘要",
                "sections": [
                    {"heading": "标题规则", "content": "..."},
                    {"heading": "钩子类型分布", "content": "..."},
                    ...
                ],
                "hot_topics": [...],
                "best_posting_times": [...],
                "generated_at": "2026-07-04T...",
            }
        """
        filepath = self._rules_dir / f"{platform}.json"
        if not filepath.exists():
            return {"error": f"{platform} 规则文件不存在", "platform": platform}

        with open(filepath, "r", encoding="utf-8") as f:
            rules = json.load(f)

        sections = []

        # 1. 标题规则
        title_rules = rules.get("title_rules", [])
        if title_rules:
            lines = ["| 类型 | 公式 | CTR评级 | 示例 |"]
            lines.append("|------|------|---------|------|")
            for tr in title_rules[:6]:
                lines.append(
                    f"| {tr.get('type', '')} "
                    f"| {tr.get('formula', '')} "
                    f"| {tr.get('ctr_rating', '')} "
                    f"| {tr.get('example', '')} |"
                )
            sections.append({"heading": "高CTR标题公式", "content": "\n".join(lines)})

        # 2. 钩子类型分布
        hook_patterns = rules.get("hook_patterns", [])
        if hook_patterns:
            lines = ["| 钩子类型 | 出现频率 | 说明 |"]
            lines.append("|----------|----------|------|")
            for hp in hook_patterns[:8]:
                count = hp.get("count", 0)
                bar = "█" * min(count // 5, 10) if count else ""
                lines.append(
                    f"| {hp.get('type', '')} "
                    f"| {count}次 {bar} "
                    f"| {hp.get('description', '')} |"
                )
            sections.append({"heading": "钩子类型分布", "content": "\n".join(lines)})

        # 3. 算法参数
        algorithm = rules.get("algorithm", {})
        if algorithm:
            lines = ["| 参数 | 值 |"]
            lines.append("|------|-----|")
            for key, val in algorithm.items():
                if isinstance(val, (str, int, float)):
                    lines.append(f"| {key} | {val} |")
                elif isinstance(val, dict):
                    for sub_key, sub_val in val.items():
                        lines.append(f"| {key} → {sub_key} | {sub_val} |")
            sections.append({"heading": "平台算法参数", "content": "\n".join(lines[:15])})

        # 4. 最佳实践
        best_practices = rules.get("best_practices", [])
        if best_practices:
            items = [f"{i + 1}. {bp}" for i, bp in enumerate(best_practices[:8])]
            sections.append({"heading": "爆款最佳实践", "content": "\n".join(items)})

        # 5. 热门话题
        trending_topics = rules.get("trending_topics", [])
        hot_topics = []
        for t in trending_topics[:15]:
            if isinstance(t, str):
                hot_topics.append(t)
            elif isinstance(t, dict):
                hot_topics.append(t.get("topic", t.get("title", "")))

        # 6. 最佳发布时间
        from monitors.analyzer import RuleAnalyzer
        posting_info = RuleAnalyzer.get_best_posting_time(platform)

        # 摘要
        total_rules = len(title_rules)
        total_hooks = len(hook_patterns)
        core_metric = algorithm.get("core_metric", "互动率") if algorithm else "互动率"

        summary = (
            f"{platform}平台当前共有 {total_rules} 种高效标题模式、{total_hooks} 种钩子类型。"
            f"算法核心指标为{core_metric}，"
            f"热门内容趋势集中在{'、'.join(hot_topics[:3])}等领域。"
        )

        return {
            "platform": platform,
            "title": f"{platform}爆款规则分析报告",
            "summary": summary,
            "sections": sections,
            "hot_topics": hot_topics,
            "best_posting_times": posting_info.get("time_slots", []),
            "best_posting_recommendation": posting_info.get("recommendation", ""),
            "core_metric": core_metric,
            "category": rules.get("category", ""),
            "last_updated": rules.get("last_updated", ""),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def generate_all_reports(self) -> list[dict]:
        """生成所有 13 个平台的报告摘要。"""
        reports = []
        for filepath in sorted(self._rules_dir.glob("*.json")):
            if filepath.name.startswith("_"):
                continue
            platform = filepath.stem
            try:
                report = self.generate_platform_report(platform)
                if "error" not in report:
                    # 只保留摘要部分
                    reports.append({
                        "platform": platform,
                        "title": report["title"],
                        "summary": report["summary"],
                        "core_metric": report.get("core_metric", ""),
                        "hot_topics": report.get("hot_topics", [])[:5],
                        "best_posting_recommendation": report.get("best_posting_recommendation", ""),
                        "category": report.get("category", ""),
                    })
            except Exception as e:
                logger.warning(f"生成{platform}报告失败: {e}")
        return reports

    def to_markdown(self, report: dict) -> str:
        """将报告 dict 渲染为 Markdown 文本。"""
        if "error" in report:
            return f"# {report['platform']}\n\n> ❌ {report['error']}"

        lines = [
            f"# {report['title']}",
            "",
            f"> {report['summary']}",
            "",
            f"**平台分类**：{report.get('category', '')}",
            f"**核心指标**：{report.get('core_metric', '')}",
            f"**规则更新时间**：{report.get('last_updated', '')}",
            "",
        ]

        # 热门话题
        hot = report.get("hot_topics", [])
        if hot:
            lines.append("## 🔥 当前热门话题")
            lines.append("")
            lines.append("、".join(hot[:15]))
            lines.append("")

        # 最佳发布时间
        posting_rec = report.get("best_posting_recommendation", "")
        if posting_rec:
            lines.append(f"## ⏰ 最佳发布时间")
            lines.append("")
            lines.append(f"> {posting_rec}")
            lines.append("")

        # 各节
        for section in report.get("sections", []):
            lines.append(f"## {section['heading']}")
            lines.append("")
            lines.append(section["content"])
            lines.append("")

        # 页脚
        lines.append("---")
        lines.append(f"*本报告由智媒圈 AI 自动生成 | {report.get('generated_at', '')}*")
        lines.append(f"*获取更多平台的实时爆款规则分析，请访问智媒圈*")

        return "\n".join(lines)

    def to_html_snippet(self, report: dict) -> str:
        """将报告渲染为适合网页展示的 HTML 片段（不含 head/body）。"""
        md = self.to_markdown(report)
        # 简单的 Markdown → HTML 转换
        html = md
        html = html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = html.replace("\\n", "<br>")

        # 标题转换
        import re
        html = re.sub(r'^### (.+)$', r'<h3 class="text-orange-400">\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2 class="text-white text-xl">\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1 class="text-gradient text-2xl font-bold">\1</h1>', html, flags=re.MULTILINE)

        return f'<div class="report-content">{html}</div>'
