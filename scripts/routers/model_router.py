"""模型路由 API"""

from fastapi import APIRouter
from pydantic import BaseModel

from services.router import default_router, TaskType, MODEL_PROFILES

router = APIRouter()


class RouteRequest(BaseModel):
    prompt: str
    system: str = ""
    task_type: str = "content_generation"
    priority: str = "balanced"  # cost / quality / speed / balanced


@router.post("/chat")
async def route_chat(req: RouteRequest):
    """路由到最优模型"""
    try:
        task = TaskType(req.task_type)
    except ValueError:
        task = TaskType.CONTENT_GENERATION

    result = await default_router.route(
        prompt=req.prompt,
        system=req.system,
        task_type=task,
        priority=req.priority,
    )
    return result


@router.get("/profiles")
async def list_profiles():
    """列出所有模型档案"""
    return {
        name: {
            "name": p.name,
            "cost_per_1k": p.cost_per_1k_tokens,
            "avg_latency_ms": p.avg_latency_ms,
            "quality": p.quality_score,
            "best_for": [t.value for t in p.best_for],
        }
        for name, p in MODEL_PROFILES.items()
    }


@router.get("/stats")
async def get_stats():
    """获取路由统计"""
    return default_router.get_stats()


@router.get("/recommend")
async def recommend_model(
    task_type: str = "content_generation", priority: str = "balanced"
):
    """推荐模型"""
    try:
        task = TaskType(task_type)
    except ValueError:
        task = TaskType.CONTENT_GENERATION
    return {"recommended": default_router.select_model(task, priority)}
