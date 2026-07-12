"""数据闭环 API"""

import json
from datetime import datetime
from pathlib import Path

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


class FeedbackRequest(BaseModel):
    project_id: str
    content_id: str
    platform: str
    fire_score_predicted: float | None = None
    actual_metrics: dict  # {"views": N, "likes": N, "comments": N, "shares": N, ...}


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


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    """提交实际表现数据，对比 Fire Score 预测，记录偏差供校准使用。

    闭环流程：
    1. 更新 DataTracker 中已有的发布记录
    2. 对比 predicted vs actual（基于互动率）
    3. 写入 data/calibration/ 供 calibrator 后续使用
    """
    # 1. 更新 DataTracker 记录
    tracker.update_metrics(req.project_id, req.content_id, req.actual_metrics)

    # 2. 计算实际互动率作为 actual score 的近似
    views = req.actual_metrics.get("views", 0)
    if views > 0:
        likes = req.actual_metrics.get("likes", 0)
        comments = req.actual_metrics.get("comments", 0)
        shares = req.actual_metrics.get("shares", 0)
        actual_engagement = round((likes + comments + shares) / views * 100, 2)
    else:
        actual_engagement = 0.0

    # 3. 记录偏差到 calibration 目录
    deviation = {
        "project_id": req.project_id,
        "content_id": req.content_id,
        "platform": req.platform,
        "fire_score_predicted": req.fire_score_predicted,
        "actual_metrics": req.actual_metrics,
        "actual_engagement_pct": actual_engagement,
        "deviation": round((req.fire_score_predicted or 0) - actual_engagement, 2),
        "recorded_at": datetime.now().isoformat(),
    }

    cal_dir = Path("../data/calibration")
    cal_dir.mkdir(parents=True, exist_ok=True)
    cal_file = cal_dir / f"{req.project_id}_{req.content_id}.json"
    with open(cal_file, "w", encoding="utf-8") as f:
        json.dump(deviation, f, ensure_ascii=False, indent=2)

    return deviation
