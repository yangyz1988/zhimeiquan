"""内容改写引擎 - 将低分内容自动优化至 95+ Fire Score

支持单条改写、批量改写、跨平台适配以及版本对比。
集成 Fire Score 评分体系、模型路由、缓存和平台规则。

Usage:
    rewriter = ContentRewriter()
    result = await rewriter.rewrite(content, platform="抖音")
    improved = await rewriter.batch_rewrite(contents, platform="小红书")
    adapted = await rewriter.rewrite_for_platform(content, "抖音", "B站")
    diff = rewriter.compare_versions(original, rewritten)
"""

import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from services.logging import logger, track_time
from services.router import default_router, TaskType
from services.cache import cache_result
from services.error_handler import retry, ai_circuit_breaker, ServiceError
from services.prompts import Prompts
from monitors.scheduler import RuleScheduler


# ──────────────────────────────────────────────
#  数据模型
# ──────────────────────────────────────────────


@dataclass
class Content:
    """内容数据模型"""
    title: str = ""
    body: str = ""
    hook: str = ""
    tags: list[str] = field(default_factory=list)
    call_to_action: str = ""
    subtitles: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Content":
        return cls(
            title=data.get("title", ""),
            body=data.get("body", data.get("script", "")),
            hook=data.get("hook", ""),
            tags=data.get("tags", []),
            call_to_action=data.get("call_to_action", ""),
            subtitles=data.get("subtitles", []),
        )

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class FireScore:
    """Fire Score 五维评分结果"""
    hook: float = 0.0
    trust: float = 0.0
    retention: float = 0.0
    conversion: float = 0.0
    emotion: float = 0.0
    total: float = 0.0
    level: str = "Lv5 基础"
    suggestions: list[str] = field(default_factory=list)
    analysis: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "FireScore":
        scores = data.get("scores", data)
        total = scores.get("total", 0)
        if isinstance(total, dict):
            total = total.get("total", 0)
        return cls(
            hook=scores.get("hook", 0),
            trust=scores.get("trust", 0),
            retention=scores.get("retention", 0),
            conversion=scores.get("conversion", 0),
            emotion=scores.get("emotion", 0),
            total=float(total),
            level=scores.get("level", data.get("level", "Lv5 基础")),
            suggestions=scores.get("suggestions", data.get("suggestions", [])),
            analysis=scores.get("analysis", data.get("analysis", "")),
        )

    @property
    def weak_dimensions(self) -> list[tuple[str, float, float]]:
        """返回低于阈值 (80) 的维度列表: [(name, score, weight), ...]"""
        dimensions = [
            ("hook", self.hook, 0.25),
            ("trust", self.trust, 0.20),
            ("retention", self.retention, 0.20),
            ("conversion", self.conversion, 0.20),
            ("emotion", self.emotion, 0.15),
        ]
        return [(n, s, w) for n, s, w in dimensions if s < 80]

    @property
    def is_good(self) -> bool:
        """是否已达目标质量"""
        return self.total >= 95


# ──────────────────────────────────────────────
#  平台映射
# ──────────────────────────────────────────────


PLATFORM_MAPPING: dict[str, str] = {
    "抖音": "douyin",
    "小红书": "xiaohongshu",
    "B站": "bilibili",
    "微博": "weibo",
    "知乎": "zhihu",
    "公众号": "wechat",
    "微信视频号": "wechat_video",
    "YouTube": "youtube",
    "TikTok": "tiktok",
    "快手": "kuaishou",
    "Instagram": "instagram",
    "Twitter": "twitter",
    "Facebook": "facebook",
}

# 跨平台适配规则 — 改写方向提示词
CROSS_PLATFORM_RULES: dict[tuple[str, str], str] = {
    ("抖音", "小红书"): "缩短时长，强化干货密度，增加emoji和分段，首图要点明核心看点",
    ("抖音", "B站"): "延长内容深度，增加数据分析，前5秒用高能片段引入，适合5-15分钟",
    ("小红书", "抖音"): "加快节奏，前3秒强钩子，使用热门BGM，时长15-60秒",
    ("小红书", "B站"): "提升内容深度和系统性，增加弹幕互动设计，时长提升至5-15分钟",
    ("B站", "抖音"): "大幅缩短时长，前3秒反问/数字钩子，保留核心亮点，15-60秒",
    ("B站", "小红书"): "提炼精华要点，图文并茂风格，增加emoji和分段，首图精美",
}


# ──────────────────────────────────────────────
#  日志工具
# ──────────────────────────────────────────────


def _log_rewrite(
    content_id: str,
    platform: str,
    original_score: float,
    new_score: float,
    changes: dict,
    metadata: dict | None = None,
):
    """将改写记录写入 data/rewrites/ 目录"""
    log_dir = Path("data/rewrites")
    log_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "content_id": content_id,
        "platform": platform,
        "timestamp": datetime.now().isoformat(),
        "original_score": original_score,
        "new_score": new_score,
        "delta": round(new_score - original_score, 1),
        "changes": changes,
        "metadata": metadata or {},
    }

    log_file = log_dir / f"rewrite_{content_id}.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    logger.info(
        "改写记录已保存",
        content_id=content_id[:16],
        platform=platform,
        delta=record["delta"],
        file=str(log_file),
    )


# ──────────────────────────────────────────────
#  ContentRewriter
# ──────────────────────────────────────────────


class ContentRewriter:
    """内容改写引擎 - 将低分内容自动优化至 95+ Fire Score

    工作流程:
    1. 解析输入内容（title, body, hook, tags 等字段）
    2. 调用 Fire Score 五维评分，识别薄弱维度
    3. 根据薄弱维度和平台规则，用 LLM 针对性改写
    4. 再次评分验证，如未达 95+ 则迭代优化（最多 3 轮）
    5. 记录改写日志到 data/rewrites/
    """

    def __init__(self, data_dir: str | None = None):
        self.router = default_router
        self.scheduler = RuleScheduler(data_dir=data_dir or "../data/rules")
        self._rewrite_count = 0

    # ── 评分 ──────────────────────────────────

    async def _score_content(self, content: Content, platform: str) -> FireScore:
        """使用 Fire Score 体系对内容进行五维评分"""
        try:
            system, prompt = Prompts.score_content(
                title=content.title,
                body=content.body,
                platform=platform,
                rules=self._load_rules(platform),
            )
            result = await ai_circuit_breaker.acall(
                self.router.route,
                prompt=prompt,
                system=system,
                task_type=TaskType.SCORING,
            )
            data = json.loads(result["result"])
            return FireScore.from_dict(data)
        except json.JSONDecodeError:
            logger.warning("评分返回格式异常，使用默认评分")
            return FireScore(total=60, level="Lv5 基础")
        except Exception as e:
            logger.error("评分失败", error=str(e))
            raise ServiceError(f"内容评分失败: {e}", code="score_failed")

    # ── 规则加载 ──────────────────────────────

    def _load_rules(self, platform: str) -> dict | None:
        """加载平台爆款规则"""
        try:
            return self.scheduler.load_rules(platform)
        except Exception:
            logger.warning(f"平台规则加载失败，使用默认规则", platform=platform)
            return None

    # ── 改写提示词构建 ───────────────────────

    def _build_rewrite_system_prompt(
        self,
        platform: str,
        weak_dimensions: list[tuple[str, float, float]],
        rules: dict | None = None,
    ) -> str:
        """构建改写任务系统提示"""
        lines = [
            "你是智媒圈AI助手，专业的自媒体内容改写专家。请用中文回复。",
            "",
            "你的任务是将给定的内容改写优化，使 Fire Score 达到 95 分以上。",
            f"目标平台：{platform}",
            "",
            "## 当前薄弱维度（需要重点优化）",
        ]

        if weak_dimensions:
            dim_names = {
                "hook": "钩子力（25%）- 前3秒能否让人停住",
                "trust": "信任度（20%）- 内容是否可信",
                "retention": "完播力（20%）- 节奏是否紧凑",
                "conversion": "转化力（20%）- 能否让用户互动",
                "emotion": "情绪值（15%）- 情绪共鸣",
            }
            for name, score, weight in weak_dimensions:
                desc = dim_names.get(name, name)
                lines.append(f"- {desc} | 当前得分: {score}/100 | 权重")
            lines.append("")
            lines.append("请针对以上薄弱维度重点优化。")
        else:
            lines.append("- 所有维度均良好，请保持优势并微调到极致。")

        if rules:
            lines.append("")
            lines.append("## 当前平台爆款规则")
            rules_text = json.dumps(rules, ensure_ascii=False, indent=2)
            lines.append(rules_text)

        lines.append("")
        lines.append(
            "请按以下JSON格式返回改写结果：\n"
            '{\n'
            '  "title": "优化后的标题",\n'
            '  "body": "优化后的正文/脚本",\n'
            '  "hook": "优化后的前3秒钩子",\n'
            '  "tags": ["标签1", "标签2"],\n'
            '  "call_to_action": "优化后的引导语",\n'
            '  "changes_summary": "改写了哪些部分及原因"\n'
            '}'
        )

        return "\n".join(lines)

    def _build_rewrite_user_prompt(self, content: Content) -> str:
        """构建改写任务用户提示"""
        return (
            "请改写以下内容：\n\n"
            f"标题：{content.title}\n"
            f"正文：{content.body}\n"
            f"钩子：{content.hook}\n"
            f"标签：{' '.join(content.tags) if content.tags else '无'}\n"
            f"引导语：{content.call_to_action or '无'}\n"
        )

    # ── 核心改写逻辑 ─────────────────────────

    @retry(max_attempts=2, delay=1.0, backoff=2.0)
    async def rewrite(
        self,
        content: dict,
        platform: str,
        target_score: int = 95,
        max_iterations: int = 3,
    ) -> dict:
        """单条内容改写

        Args:
            content: 待改写内容字典 (title, body, hook, tags, ...)
            platform: 目标平台名称（如 "抖音", "小红书"）
            target_score: 目标 Fire Score（默认 95）
            max_iterations: 最大迭代优化轮次（默认 3）

        Returns:
            改写结果字典，包含 rewritten 内容、评分变化和修改记录
        """
        content_obj = Content.from_dict(content)
        content_id = content.get("id", f"rewrite_{int(time.time())}")

        with track_time("rewrite", platform=platform, target=target_score):
            # 1. 评分当前内容
            original_score = await self._score_content(content_obj, platform)
            logger.info(
                "原始评分",
                content_id=content_id[:16],
                platform=platform,
                total=original_score.total,
                level=original_score.level,
            )

            # 2. 如果已达标，直接返回
            if original_score.is_good:
                logger.info("内容已达目标分数，无需改写", score=original_score.total)
                return {
                    "content_id": content_id,
                    "original": content_obj.to_dict(),
                    "rewritten": content_obj.to_dict(),
                    "original_score": asdict(original_score),
                    "new_score": asdict(original_score),
                    "improved": False,
                    "iterations": 0,
                    "changes": {"summary": "无需改写，已达目标分数"},
                }

            # 3. 迭代改写
            current = content_obj
            current_score = original_score
            all_changes = []
            iteration = 0

            for iteration in range(1, max_iterations + 1):
                weak = current_score.weak_dimensions
                logger.info(
                    f"第 {iteration} 轮改写",
                    content_id=content_id[:16],
                    weak_count=len(weak),
                )

                # 构建改写提示
                rules = self._load_rules(platform)
                system = self._build_rewrite_system_prompt(
                    platform, weak, rules
                )
                user_prompt = self._build_rewrite_user_prompt(current)

                # 调用 LLM
                try:
                    result = await ai_circuit_breaker.acall(
                        self.router.route,
                        prompt=user_prompt,
                        system=system,
                        task_type=TaskType.CONTENT_GENERATION,
                    )
                    data = json.loads(result["result"])
                except Exception as e:
                    logger.error(f"第 {iteration} 轮改写失败", error=str(e))
                    break

                # 更新内容
                current.title = data.get("title", current.title)
                current.body = data.get("body", current.body)
                current.hook = data.get("hook", current.hook)
                current.tags = data.get("tags", current.tags)
                current.call_to_action = data.get(
                    "call_to_action", current.call_to_action
                )
                all_changes.append(data.get("changes_summary", ""))

                # 重新评分
                current_score = await self._score_content(current, platform)

                if current_score.total >= target_score:
                    logger.info(
                        "改写达标",
                        iteration=iteration,
                        score=current_score.total,
                    )
                    break

            # 4. 记录改写日志
            changes = {"summary": " | ".join(filter(None, all_changes))}
            _log_rewrite(
                content_id=content_id,
                platform=platform,
                original_score=original_score.total,
                new_score=current_score.total,
                changes=changes,
                metadata={"iterations": iteration, "target_score": target_score},
            )

            # 5. 返回结果
            return {
                "content_id": content_id,
                "original": content_obj.to_dict(),
                "rewritten": current.to_dict(),
                "original_score": asdict(original_score),
                "new_score": asdict(current_score),
                "improved": current_score.total > original_score.total,
                "iterations": iteration,
                "changes": changes,
            }

    # ── 批量改写 ──────────────────────────────

    async def batch_rewrite(
        self,
        contents: list[dict],
        platform: str,
        target_score: int = 95,
        max_concurrent: int = 3,
    ) -> dict:
        """批量改写多条内容

        Args:
            contents: 待改写内容列表
            platform: 目标平台
            target_score: 目标 Fire Score（默认 95）
            max_concurrent: 最大并发数（默认 3）

        Returns:
            包含每条改写结果和汇总统计的字典
        """
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrent)

        async def _limited_rewrite(content: dict) -> dict:
            async with semaphore:
                return await self.rewrite(content, platform, target_score)

        results = await asyncio.gather(
            *[_limited_rewrite(c) for c in contents], return_exceptions=True
        )

        # 整理结果和统计
        rewritten_list = []
        errors = []
        total_before = 0.0
        total_after = 0.0
        improved_count = 0

        for i, res in enumerate(results):
            if isinstance(res, Exception):
                errors.append({"index": i, "error": str(res)})
                continue
            rewritten_list.append(res)
            total_before += res["original_score"]["total"]
            total_after += res["new_score"]["total"]
            if res.get("improved"):
                improved_count += 1

        n = len(rewritten_list) or 1
        stats = {
            "total": len(contents),
            "success": len(rewritten_list),
            "errors": len(errors),
            "improved": improved_count,
            "avg_original_score": round(total_before / n, 1),
            "avg_new_score": round(total_after / n, 1),
            "avg_improvement": round((total_after - total_before) / n, 1),
            "platform": platform,
            "target_score": target_score,
        }

        logger.info(
            "批量改写完成",
            total=stats["total"],
            success=stats["success"],
            avg_improvement=stats["avg_improvement"],
        )

        return {
            "results": rewritten_list,
            "errors": errors,
            "stats": stats,
        }

    # ── 跨平台改写 ───────────────────────────

    async def rewrite_for_platform(
        self,
        content: dict,
        source_platform: str,
        target_platform: str,
    ) -> dict:
        """将内容从一个平台适配到另一个平台

        例如将 抖音 口播稿改写为 小红书 图文笔记格式。

        Args:
            content: 源平台内容字典
            source_platform: 源平台名称
            target_platform: 目标平台名称

        Returns:
            适配后的内容及转换说明
        """
        content_obj = Content.from_dict(content)
        content_id = content.get("id", f"xplat_{int(time.time())}")

        # 获取跨平台适配规则
        rule_key = (source_platform, target_platform)
        reverse_key = (target_platform, source_platform)
        adapt_rule = CROSS_PLATFORM_RULES.get(rule_key) or CROSS_PLATFORM_RULES.get(
            reverse_key, "请根据目标平台特性调整内容风格和结构"
        )

        with track_time(
            "rewrite_for_platform",
            source=source_platform,
            target=target_platform,
        ):
            # 加载目标平台规则
            target_rules = self._load_rules(target_platform)

            system = (
                f"你是智媒圈AI助手，擅长跨平台内容适配。\n"
                f"源平台：{source_platform}\n"
                f"目标平台：{target_platform}\n\n"
                f"适配要点：{adapt_rule}\n\n"
                f"目标平台爆款规则：\n"
                f"{json.dumps(target_rules, ensure_ascii=False, indent=2)}\n\n"
                "请按以下JSON格式返回转换结果：\n"
                '{\n'
                '  "title": "适配后的标题",\n'
                '  "body": "适配后的正文/脚本",\n'
                '  "hook": "适配后的钩子",\n'
                '  "tags": ["标签1", "标签2"],\n'
                '  "call_to_action": "适配后的引导语",\n'
                '  "adaptation_notes": "做了哪些适配调整"\n'
                '}'
            )

            user_prompt = (
                f"请将以下{source_platform}内容适配为{target_platform}格式：\n\n"
                f"标题：{content_obj.title}\n"
                f"正文：{content_obj.body}\n"
                f"钩子：{content_obj.hook}\n"
                f"标签：{' '.join(content_obj.tags) if content_obj.tags else '无'}\n"
            )

            try:
                result = await ai_circuit_breaker.acall(
                    self.router.route,
                    prompt=user_prompt,
                    system=system,
                    task_type=TaskType.CONTENT_GENERATION,
                )
                data = json.loads(result["result"])
            except Exception as e:
                raise ServiceError(f"跨平台适配失败: {e}", code="xplat_failed")

            adapted = Content(
                title=data.get("title", content_obj.title),
                body=data.get("body", content_obj.body),
                hook=data.get("hook", content_obj.hook),
                tags=data.get("tags", content_obj.tags),
                call_to_action=data.get("call_to_action", content_obj.call_to_action),
            )

            # 评分适配后内容
            adapted_score = await self._score_content(adapted, target_platform)

            _log_rewrite(
                content_id=content_id,
                platform=target_platform,
                original_score=0,
                new_score=adapted_score.total,
                changes={
                    "type": "cross_platform",
                    "source": source_platform,
                    "target": target_platform,
                    "notes": data.get("adaptation_notes", ""),
                },
            )

            return {
                "content_id": content_id,
                "source_platform": source_platform,
                "target_platform": target_platform,
                "original": content_obj.to_dict(),
                "rewritten": adapted.to_dict(),
                "target_score": asdict(adapted_score),
                "adaptation_notes": data.get("adaptation_notes", ""),
                "model": result.get("model", ""),
            }

    # ── 版本对比 ─────────────────────────────

    @staticmethod
    def compare_versions(original: dict, rewritten: dict) -> dict:
        """对比改写前后的版本差异

        对比所有关键字段（title, body, hook, tags, call_to_action），
        找出具体改动并提供结构化 diff 信息。

        Args:
            original: 原始内容字典
            rewritten: 改写后内容字典

        Returns:
            包含所有字段差异的对比结果
        """
        fields = ["title", "body", "hook", "tags", "call_to_action"]
        diffs = {}

        for field in fields:
            old_val = original.get(field, "")
            new_val = rewritten.get(field, "")

            if old_val == new_val:
                continue

            if field == "tags":
                old_set = set(old_val) if isinstance(old_val, list) else set()
                new_set = set(new_val) if isinstance(new_val, list) else set()
                diffs[field] = {
                    "changed": True,
                    "old": list(old_val) if isinstance(old_val, list) else old_val,
                    "new": list(new_val) if isinstance(new_val, list) else new_val,
                    "added": list(new_set - old_set),
                    "removed": list(old_set - new_set),
                }
            else:
                diffs[field] = {
                    "changed": True,
                    "old": old_val,
                    "new": new_val,
                    "old_length": len(str(old_val)),
                    "new_length": len(str(new_val)),
                }

        summary = "无变化"
        if diffs:
            changed_fields = list(diffs.keys())
            summary = f"修改了 {len(diffs)} 个字段: {', '.join(changed_fields)}"

        return {
            "summary": summary,
            "changed_fields": list(diffs.keys()),
            "total_changes": len(diffs),
            "diffs": diffs,
        }

    # ── 统计 ─────────────────────────────────

    def get_stats(self) -> dict:
        """获取改写引擎使用统计"""
        return {
            "total_rewrites": self._rewrite_count,
            "router_stats": self.router.get_stats(),
        }
