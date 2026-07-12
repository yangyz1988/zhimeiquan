"""Fire Score 校准 API 路由"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from analyzers.calibrator import FireScoreCalibrator
from analyzers.data_tracker import DataTracker

router = APIRouter()

calibrator = FireScoreCalibrator()
tracker = DataTracker()


class PerformanceReportRequest(BaseModel):
    content_id: str
    user_id: str
    platform: str
    fire_score: float | None = None
    dimension_scores: dict[str, float] | None = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    favorites: int = 0


class CalibrateRequest(BaseModel):
    user_id: str
    platform: str


class WeightResponse(BaseModel):
    hook: float
    trust: float
    retention: float
    conversion: float
    emotion: float


@router.post("/report")
async def report_performance(req: PerformanceReportRequest):
    """用户上报发布后数据，触发 Fire Score 校准

    数据流：
    1. 先创建发布记录 (record_publish)
    2. 再更新指标数据 (update_metrics)
    3. 最后触发校准 (calibrator)
    """
    # 第一步：创建发布记录
    tracker.record_publish(
        content_id=req.content_id,
        user_id=req.user_id,
        platform=req.platform,
        title="",
        fire_score=req.fire_score,
        dimension_scores=req.dimension_scores,
    )

    # 第二步：更新指标数据
    record = tracker.update_metrics(
        req.content_id,
        {
            "views": req.views,
            "likes": req.likes,
            "comments": req.comments,
            "shares": req.shares,
            "favorites": req.favorites,
        },
    )

    # 第三步：记录到校准器
    calibrator.record_performance(
        req.content_id,
        req.user_id,
        req.platform,
        req.fire_score,
        req.dimension_scores,
        {
            "views": req.views,
            "likes": req.likes,
            "comments": req.comments,
            "shares": req.shares,
            "favorites": req.favorites,
        },
    )

    # 第四步：运行校准
    result = calibrator.calibrate(req.user_id, req.platform)

    return {
        "engagement_rate": record.get("engagement_rate", 0),
        "calibration": result,
    }


@router.get("/weights/{platform}")
async def get_weights(platform: str, user_id: str = "default"):
    """获取某平台当前的 Fire Score 权重"""
    weights = calibrator.get_calibrated_weights(user_id, platform)
    history = tracker.get_platform_history(user_id, platform, limit=5)

    return {
        "user_id": user_id,
        "platform": platform,
        "weights": weights,
        "recent_content_count": len(history),
    }


@router.post("/calibrate")
async def calibrate_weights(req: CalibrateRequest):
    """手动触发权重校准"""
    result = calibrator.calibrate(req.user_id, req.platform)
    accuracy = tracker.get_fire_score_accuracy(req.user_id, req.platform)

    return {
        "calibration": result,
        "accuracy": accuracy,
    }
