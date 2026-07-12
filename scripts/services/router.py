"""智能模型路由 - 根据任务选择最优模型（强化学习版）"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
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
    cost_per_1k_tokens: float  # 每1K token 成本（元）
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

# 模型建议的默认 token 价格（用于成本估算）
MODEL_INPUT_PRICES = {
    "deepseek": 0.0005,  # 每1K tokens 输入价格（元）
    "qwen": 0.002,
    "ernie": 0.003,
    "hunyuan": 0.003,
}

MODEL_OUTPUT_PRICES = {
    "deepseek": 0.002,
    "qwen": 0.006,
    "ernie": 0.006,
    "hunyuan": 0.008,
}

# 记录保留天数
HISTORY_RETENTION_DAYS = 30


@dataclass
class RoutingStrategy:
    """路由策略"""

    prefer: str = "balanced"  # cost / quality / speed / balanced
    fallback: bool = True  # 失败时是否降级
    max_retries: int = 2
    excluded_models: list[str] = field(default_factory=list)
    use_learned: bool = True  # 是否使用历史学习数据


class ModelRouter:
    """智能模型路由器（支持学习优化）"""

    def __init__(
        self,
        strategy: RoutingStrategy | None = None,
        history_dir: str | None = None,
    ):
        self.strategy = strategy or RoutingStrategy()
        self.call_history: list[dict] = []
        self.history_dir = Path(history_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "router_history"))
        self._ensure_history_dir()

    # ========== 历史数据管理 ==========

    def _ensure_history_dir(self):
        """确保历史数据目录存在"""
        self.history_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"路由历史目录已就绪", path=str(self.history_dir))

    def _build_history_path(self, date_str: str | None = None) -> Path:
        """构建当天或指定日期的历史文件路径"""
        date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        return self.history_dir / f"calls_{date_str}.jsonl"

    def _load_history(self, days: int = 30) -> list[dict]:
        """从文件加载历史数据（最近N天）"""
        records = []
        try:
            from datetime import timedelta
            for i in range(days):
                date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                file_path = self._build_history_path(date_str)
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    records.append(json.loads(line))
                                except json.JSONDecodeError:
                                    continue
        except Exception as e:
            logger.warning(f"加载路由历史失败", error=str(e))
        return records

    def record_result(self, call_data: dict):
        """记录一次路由结果用于学习"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "model_name": call_data.get("model_name", "unknown"),
            "task_type": call_data.get("task_type", "unknown"),
            "duration_ms": call_data.get("duration_ms", 0),
            "success": call_data.get("success", True),
            "quality_rating": call_data.get("quality_rating"),
            "cost": call_data.get("cost"),
            "prompt_length": call_data.get("prompt_length"),
        }
        # 写入内存
        self.call_history.append(record)

        # 写入文件（JSONL 格式）
        try:
            file_path = self._build_history_path()
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning(f"写入路由历史失败", error=str(e))

    def get_model_performance(self, model_name: str | None = None) -> dict:
        """获取模型性能统计"""
        records = self._load_history()

        if not records:
            return {}

        # 筛选模型
        if model_name:
            records = [r for r in records if r["model_name"] == model_name]
            if not records:
                return {}

        # 按模型分组
        by_model: dict[str, dict] = {}
        for rec in records:
            m = rec["model_name"]
            if m not in by_model:
                by_model[m] = {
                    "total_calls": 0,
                    "success_calls": 0,
                    "total_duration_ms": 0,
                    "total_cost": 0.0,
                    "by_task": {},
                }
            stats = by_model[m]
            stats["total_calls"] += 1
            if rec["success"]:
                stats["success_calls"] += 1
            stats["total_duration_ms"] += rec.get("duration_ms", 0)
            stats["total_cost"] += rec.get("cost", 0)

            # 按任务类型细列
            task = rec.get("task_type", "unknown")
            if task not in stats["by_task"]:
                stats["by_task"][task] = {
                    "calls": 0,
                    "success": 0,
                    "total_duration_ms": 0,
                    "total_quality": 0.0,
                    "quality_count": 0,
                }
            tstats = stats["by_task"][task]
            tstats["calls"] += 1
            if rec["success"]:
                tstats["success"] += 1
            tstats["total_duration_ms"] += rec.get("duration_ms", 0)
            q = rec.get("quality_rating")
            if q is not None:
                tstats["total_quality"] += q
                tstats["quality_count"] += 1

        # 计算每个模型每个任务的统计指标
        for model_name_key, model_stats in by_model.items():
            for task_type, tstats in model_stats["by_task"].items():
                if tstats["calls"] > 0:
                    tstats["avg_duration_ms"] = tstats["total_duration_ms"] / tstats["calls"]
                    tstats["success_rate"] = tstats["success"] / tstats["calls"]
                if tstats.get("quality_count", 0) > 0:
                    tstats["avg_quality"] = tstats["total_quality"] / tstats["quality_count"]
                # 清理临时字段
                tstats.pop("total_duration_ms", None)
                tstats.pop("total_quality", None)
                tstats.pop("quality_count", None)

        return {
            "models": by_model,
            "total_calls": sum(s["total_calls"] for s in by_model.values()),
            "period": f"last {HISTORY_RETENTION_DAYS} days",
        }

    def get_optimal_model(self, task_type: TaskType, priority: str = "balanced") -> str:
        """基于历史表现自动选择最优模型"""
        history = self._load_history()
        relevant = [h for h in history if h.get("task_type") == task_type.value]
        if len(relevant) < 3:
            return self.select_model(task_type, priority)

        model_scores: dict[str, dict] = {}
        for rec in relevant:
            mn = rec.get("model_name", "")
            if mn not in model_scores:
                model_scores[mn] = {"calls": 0, "success": 0, "total_ms": 0, "total_quality": 0, "q_count": 0}
            ms = model_scores[mn]
            ms["calls"] += 1
            if rec.get("success", True):
                ms["success"] += 1
            ms["total_ms"] += rec.get("duration_ms", 0)
            q = rec.get("quality_rating")
            if q is not None:
                ms["total_quality"] += q
                ms["q_count"] += 1

        def compute_score(mn: str) -> float:
            ms = model_scores[mn]
            sr = ms["success"] / ms["calls"] if ms["calls"] > 0 else 0
            lat = 1.0 - (ms["total_ms"] / ms["calls"] / 5000) if ms["calls"] > 0 else 0.5
            qual = ms["total_quality"] / ms["q_count"] / 100 if ms["q_count"] > 0 else 0.5
            profile = MODEL_PROFILES.get(mn)
            cost = 1.0 - (profile.cost_per_1k_tokens / 0.01) if profile else 0.5
            return sr * 0.3 + qual * 0.3 + lat * 0.2 + cost * 0.2

        best_model = max(model_scores.keys(), key=compute_score)
        return best_model

    def select_model(self, task_type: TaskType, priority: str = "balanced") -> str:
        """根据策略选择模型"""
        available = [name for name in MODEL_PROFILES if name in MODELS and name not in self.strategy.excluded_models]
        
        if not available:
            return "deepseek"  # 默认模型

        if priority == "cost":
            return min(available, key=lambda n: MODEL_PROFILES[n].cost_per_1k_tokens)
        elif priority == "quality":
            return max(available, key=lambda n: MODEL_PROFILES[n].quality_score)
        elif priority == "speed":
            return min(available, key=lambda n: MODEL_PROFILES[n].avg_latency_ms)
        else:
            # balanced: 优先选择擅长该任务的模型
            for name in available:
                if task_type in MODEL_PROFILES[name].best_for:
                    return name
            return available[0]

    async def route(
        self,
        prompt: str,
        system: str = "",
        task_type: TaskType = TaskType.CHAT,
        temperature: float = 0.7,
        model: str | None = None,
    ) -> dict:
        """执行路由并调用模型"""
        # 选择模型
        if model:
            model_name = model
        elif self.strategy.use_learned:
            model_name = self.get_optimal_model(task_type, self.strategy.prefer)
        else:
            model_name = self.select_model(task_type, self.strategy.prefer)

        # 获取模型客户端
        llm = get_model(model_name)
        
        start_time = time.time()
        try:
            result = await llm.chat(prompt, system, temperature)
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 记录结果
            self.record_result({
                "model_name": model_name,
                "task_type": task_type.value,
                "duration_ms": duration_ms,
                "success": True,
                "prompt_length": len(prompt),
            })
            
            return {
                "result": result,
                "model": model_name,
                "duration_ms": duration_ms,
            }
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.record_result({
                "model_name": model_name,
                "task_type": task_type.value,
                "duration_ms": duration_ms,
                "success": False,
                "error": str(e),
            })
            raise

    def enhance_prompt(self, prompt: str, task_type: TaskType, model_name: str) -> str:
        """根据模型特性优化提示词"""
        enhancements = {
            "deepseek": {
                TaskType.CONTENT_GENERATION: "\n请逐步推理并给出完整的中文内容。",
                TaskType.ANALYSIS: "\n请分步骤分析，每一步给出推理过程。",
            },
            "qwen": {
                TaskType.TITLE_GENERATION: "\n严格按指定格式输出，确保标题简洁有力。",
                TaskType.SCORING: "\n严格按照JSON格式输出，确保所有字段完整。",
            },
            "ernie": {
                TaskType.SCORING: "\n请注意：必须输出合法的JSON格式，不要包含额外文本。",
                TaskType.ANALYSIS: "\n请基于数据进行分析，给出具体的数据支撑。",
            },
            "hunyuan": {
                TaskType.CREATIVE: "\n请发挥创意，使用生动形象的中文表达，可以适当使用修辞手法。",
                TaskType.CONTENT_GENERATION: "\n请用富有感染力的中文风格写作，注意节奏感。",
            },
        }
        extra = enhancements.get(model_name, {}).get(task_type, "")
        if extra:
            return prompt + extra
        return prompt

    def estimate_cost(self, prompt: str, model_name: str) -> float:
        """估算某次调用的成本"""
        profile = MODEL_PROFILES.get(model_name)
        if not profile:
            return 0.0
        input_tokens = len(prompt) * 1.5  # 估算：中文字符约1.5 token
        output_tokens = 500  # 预估输出
        total_tokens = (input_tokens + output_tokens) / 1000
        return round(total_tokens * profile.cost_per_1k_tokens, 4)

    def select_cheapest_model(self, task_type: TaskType, quality_min: float = 0.7) -> str:
        """选择满足质量门槛的最便宜模型"""
        available = {
            name: p for name, p in MODEL_PROFILES.items()
            if name not in self.strategy.excluded_models
            and name in MODELS
            and p.quality_score >= quality_min
        }
        if not available:
            return self.select_model(task_type, "cost")
        return min(available, key=lambda n: available[n].cost_per_1k_tokens)


# 全局实例
default_router = ModelRouter()
