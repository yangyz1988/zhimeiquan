"""模型路由测试"""

import pytest
from services.router import ModelRouter, RoutingStrategy, TaskType, MODEL_PROFILES


def test_router_default_strategy():
    router = ModelRouter()
    assert router.strategy.prefer == "balanced"
    assert router.strategy.fallback is True


def test_router_select_by_task():
    router = ModelRouter()
    # 内容生成应该选择 deepseek 或 qwen
    model = router.select_model(TaskType.CONTENT_GENERATION)
    assert model in ["deepseek", "qwen"]


def test_router_select_by_quality():
    router = ModelRouter(strategy=RoutingStrategy(prefer="quality"))
    model = router.select_model(TaskType.ANALYSIS)
    profile = MODEL_PROFILES[model]
    assert profile.quality_score >= 0.85


def test_router_select_by_cost():
    router = ModelRouter(strategy=RoutingStrategy(prefer="cost"))
    model = router.select_model(TaskType.CONTENT_GENERATION)
    assert model == "deepseek"  # deepseek 是最便宜的


def test_router_select_by_speed():
    router = ModelRouter(strategy=RoutingStrategy(prefer="speed"))
    model = router.select_model(TaskType.SCORING)
    # 应该有最低的延迟
    profile = MODEL_PROFILES[model]
    assert profile.avg_latency_ms <= 2200


def test_router_exclude_models():
    router = ModelRouter(strategy=RoutingStrategy(excluded_models=["deepseek"]))
    model = router.select_model(TaskType.CONTENT_GENERATION)
    assert model != "deepseek"


def test_router_no_available():
    router = ModelRouter(
        strategy=RoutingStrategy(excluded_models=list(MODEL_PROFILES.keys()))
    )
    with pytest.raises(ValueError, match="没有可用的模型"):
        router.select_model(TaskType.CONTENT_GENERATION)


def test_router_stats_empty():
    router = ModelRouter()
    stats = router.get_stats()
    assert stats["total"] == 0


def test_router_stats_with_calls():
    router = ModelRouter()
    router.call_history.append(
        {
            "model": "deepseek",
            "task": "content_generation",
            "duration_ms": 100,
            "success": True,
        }
    )
    stats = router.get_stats()
    assert stats["total"] == 1
    assert "deepseek" in stats["by_model"]


def test_model_profiles_have_required_fields():
    for name, profile in MODEL_PROFILES.items():
        assert profile.name
        assert profile.cost_per_1k_tokens >= 0
        assert profile.avg_latency_ms >= 0
        assert 0 <= profile.quality_score <= 1
        assert len(profile.best_for) > 0


def test_task_type_enum():
    assert TaskType.CONTENT_GENERATION.value == "content_generation"
    assert TaskType.TITLE_GENERATION.value == "title_generation"
    assert TaskType.SCORING.value == "scoring"
    assert TaskType.CREATIVE.value == "creative"
