"""数据闭环 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.data_loop import DataTracker

router = APIRouter()
tracker = DataTracker(data_dir="../data/analytics")


class PublishRequest(BaseModel):
    project_id: str
    platform: str
    title: str
    content_id: str
    fire_score: float | None = None


class MetricsRequest(BaseModel):
    metrics: dict


@router.post("/publish")
async def record_publish(req: PublishRequest):
    """记录发布事件"""
    record = tracker.record_publish(
        req.project_id,
        req.platform,
        req.title,
        req.content_id,
        fire_score=req.fire_score,
    )
    return record


@router.post("/{project_id}/{content_id}/metrics")
async def update_metrics(project_id: str, content_id: str, req: MetricsRequest):
    """更新表现数据"""
    result = tracker.update_metrics(project_id, content_id, req.metrics)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/{project_id}")
async def get_project_analytics(project_id: str):
    """获取项目分析"""
    return tracker.get_project_analytics(project_id)


@router.get("/platforms/summary")
async def get_platform_summary():
    """获取平台汇总"""
    return tracker.get_platform_summary()


@router.get("/fire-score/{project_id}")
async def get_fire_score(project_id: str):
    """获取项目平均 Fire Score"""
    avg = tracker.get_avg_fire_score(project_id)
    return {"project_id": project_id, "avg_fire_score": avg}
