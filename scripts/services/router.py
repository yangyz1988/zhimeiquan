"""智能模型路由 - 根据任务选择最优模型"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from services.models import get_model, MODELS, BaseLLM
from services.logging import logger


class TaskType(str, Enum):
    """任务类型"""

    CONTENT_GENERATION = "content_generation"  # 内容生成（长文）
    TITLE_GENERATION = "title_generation"  # 标题生成（短文）
    SCORING = "scoring"  # 评分（结构化）
    ANALYSIS = "analysis"  # 分析（深度推理）
    CREATIVE = "creative"  # 创意（高创造性）
    TRANSLATION = "translation"  # 翻译
    CHAT = "chat"  # 聊天


@dataclass
class ModelProfile:
    """模型性能档案"""

    name: str
    cost_per_1k_tokens: float  # 每 1K token 成本（元）
    avg_latency_ms: float  # 平均延迟
    quality_score: float  # 质量评分 0-1
    max_tokens: int  # 最大输出 token
    best_for: list[TaskType]  # 擅长任务


# 模型档案
MODEL_PROFILES = {
    "deepseek": ModelProfile(
        name="DeepSeek Chat",
        cost_per_1k_tokens=0.001,
        avg_latency_ms=2500,
        quality_score=0.90,
        max_tokens=4096,
        best_for=[TaskType.CONTENT_GENERATION, TaskType.ANALYSIS, TaskType.CHAT],
    ),
    "qwen": ModelProfile(
        name="通义千问 Turbo",
        cost_per_1k_tokens=0.003,
        avg_latency_ms=2000,
        quality_score=0.85,
        max_tokens=6000,
        best_for=[
            TaskType.CONTENT_GENERATION,
            TaskType.TITLE_GENERATION,
            TaskType.TRANSLATION,
        ],
    ),
    "ernie": ModelProfile(
        name="文心一言 Speed",
        cost_per_1k_tokens=0.004,
        avg_latency_ms=1800,
        quality_score=0.82,
        max_tokens=8000,
        best_for=[TaskType.SCORING, TaskType.ANALYSIS],
    ),
    "hunyuan": ModelProfile(
        name="混元 Standard",
        cost_per_1k_tokens=0.005,
        avg_latency_ms=2200,
        quality_score=0.83,
        max_tokens=4000,
        best_for=[TaskType.CREATIVE, TaskType.CHAT],
    ),
}


@dataclass
class RoutingStrategy:
    """路由策略"""

    prefer: str = "balanced"  # cost / quality / speed / balanced
    fallback: bool = True  # 失败时是否降级
    max_retries: int = 2
    excluded_models: list[str] = field(default_factory=list)


class ModelRouter:
    """智能模型路由器"""

    def __init__(self, strategy: RoutingStrategy | None = None):
        self.strategy = strategy or RoutingStrategy()
        self.call_history: list[dict] = []

    def select_model(
        self,
        task_type: TaskType,
        priority: str | None = None,
    ) -> str:
        """根据任务和策略选择最优模型"""
        priority = priority or self.strategy.prefer
        available = {
            name: profile
            for name, profile in MODEL_PROFILES.items()
            if name not in self.strategy.excluded_models and name in MODELS
        }

        if not available:
            raise ValueError("没有可用的模型")

        # 根据任务类型筛选
        suitable = {name: p for name, p in available.items() if task_type in p.best_for}

        # 如果没有特别擅长的，使用所有可用模型
        if not suitable:
            suitable = available

        if priority == "cost":
            return min(suitable, key=lambda n: suitable[n].cost_per_1k_tokens)
        elif priority == "speed":
            return min(suitable, key=lambda n: suitable[n].avg_latency_ms)
        elif priority == "quality":
            return max(suitable, key=lambda n: suitable[n].quality_score)
        else:  # balanced
            # 加权评分：质量 0.5 + 速度 0.3 + 成本 0.2
            def score(p: ModelProfile) -> float:
                # 归一化
                quality = p.quality_score
                speed = 1.0 - (p.avg_latency_ms / 5000)
                cost = 1.0 - (p.cost_per_1k_tokens / 0.01)
                return quality * 0.5 + speed * 0.3 + cost * 0.2

            return max(suitable, key=lambda n: score(suitable[n]))

    async def route(
        self,
        prompt: str,
        system: str = "",
        task_type: TaskType = TaskType.CONTENT_GENERATION,
        priority: str | None = None,
    ) -> dict[str, Any]:
        """路由到最优模型并执行"""
        start = time.time()
        model_name = self.select_model(task_type, priority)
        profile = MODEL_PROFILES[model_name]

        try:
            model = get_model(model_name)
            result = await model.chat(prompt, system=system)

            duration = (time.time() - start) * 1000

            self.call_history.append(
                {
                    "model": model_name,
                    "task": task_type.value,
                    "duration_ms": duration,
                    "success": True,
                }
            )

            return {
                "result": result,
                "model": model_name,
                "model_name": profile.name,
                "duration_ms": duration,
                "task": task_type.value,
            }

        except Exception as e:
            if self.strategy.fallback:
                return await self._fallback(
                    prompt,
                    system,
                    task_type,
                    priority,
                    exclude=[model_name],
                    error=str(e),
                )
            raise

    async def _fallback(
        self,
        prompt: str,
        system: str,
        task_type: TaskType,
        priority: str | None,
        exclude: list[str],
        error: str,
    ) -> dict[str, Any]:
        """降级到备选模型"""
        logger.warning(f"模型 {exclude[0]} 失败，降级", error=error)

        # 创建临时策略排除失败的模型
        old_excluded = self.strategy.excluded_models
        self.strategy.excluded_models = list(set(old_excluded + exclude))

        try:
            model_name = self.select_model(task_type, priority)
            model = get_model(model_name)
            result = await model.chat(prompt, system=system)
            return {
                "result": result,
                "model": model_name,
                "model_name": MODEL_PROFILES[model_name].name,
                "task": task_type.value,
                "fallback": True,
            }
        finally:
            self.strategy.excluded_models = old_excluded

    def get_stats(self) -> dict:
        """获取使用统计"""
        if not self.call_history:
            return {"total": 0}

        by_model = {}
        for call in self.call_history:
            m = call["model"]
            if m not in by_model:
                by_model[m] = {"count": 0, "success": 0, "total_ms": 0}
            by_model[m]["count"] += 1
            if call["success"]:
                by_model[m]["success"] += 1
            by_model[m]["total_ms"] += call.get("duration_ms", 0)

        for m in by_model:
            cnt = by_model[m]["count"]
            by_model[m]["avg_ms"] = by_model[m]["total_ms"] / cnt
            by_model[m]["success_rate"] = by_model[m]["success"] / cnt

        return {
            "total": len(self.call_history),
            "by_model": by_model,
        }


# 全局实例
default_router = ModelRouter()
