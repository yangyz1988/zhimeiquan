"""Fire Score 校准 API 路由 — 权重调整与校准状态

端点:
- POST /api/v1/calibrate/weights  调整 Fire Score 五维权重
- GET  /api/v1/calibrate/status   获取校准状态与历史
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from analyzers.calibrator import (
    FireScoreCalibrator,
    DEFAULT_WEIGHTS,
    DIMENSIONS,
    MIN_SAMPLES,
)

router = APIRouter()
calibrator = FireScoreCalibrator()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class AdjustWeightsRequest(BaseModel):
    user_id: str = Field(..., description="用户 ID", min_length=1, max_length=128)
    platform: str = Field(..., description="平台名称", min_length=1, max_length=64)
    method: str = Field(
        default="sliding_window",
        description="校准方法: sliding_window | full_history",
        pattern=r"^(sliding_window|full_history)$",
    )


class ManualWeightsRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    platform: str = Field(..., min_length=1, max_length=64)
    weights: dict[str, float] = Field(
        ...,
        description="手动设置的权重，键为 hook/trust/retention/conversion/emotion",
    )


class WeightItem(BaseModel):
    hook: float
    trust: float
    retention: float
    conversion: float
    emotion: float


class CalibrationStatusResponse(BaseModel):
    user_id: str
    platform: str
    weights: WeightItem
    default_weights: WeightItem
    sample_count: int
    data_quality: str
    last_calibrated_at: str | None


# ---------------------------------------------------------------------------
# POST /api/v1/calibrate/weights
# ---------------------------------------------------------------------------

@router.post("/weights", summary="调整 Fire Score 权重")
async def adjust_weights(req: AdjustWeightsRequest):
    """根据历史发布数据自动校准 Fire Score 五维权重。

    支持两种方法：
    - **sliding_window**（默认）：使用最近 50 条记录，适合快速迭代
    - **full_history**：使用全部历史数据并施加 15% 偏差封顶，适合稳定校准

    返回校准后的权重、相关性分析、稳定性检查结果。
    """
    if req.method == "full_history":
        result = calibrator.calibrate_from_history(req.user_id, req.platform)
    else:
        result = calibrator.calibrate(req.user_id, req.platform)

    if result["status"] == "insufficient_data":
        raise HTTPException(
            status_code=422,
            detail={
                "code": "insufficient_data",
                "message": result.get("message", f"至少需要 {MIN_SAMPLES} 条数据"),
                "sample_count": result.get("sample_count", 0),
                "weights": result.get("weights"),
            },
        )

    return result


@router.put("/weights", summary="手动覆盖 Fire Score 权重")
async def set_manual_weights(req: ManualWeightsRequest):
    """手动设置 Fire Score 五维权重，跳过自动校准。

    权重总和将自动归一化为 100%。
    """
    valid_dims = set(DIMENSIONS)
    provided = set(req.weights.keys())

    missing = valid_dims - provided
    if missing:
        raise HTTPException(
            status_code=422,
            detail={"code": "missing_dimensions", "message": f"缺少维度: {', '.join(sorted(missing))}"},
        )

    unknown = provided - valid_dims
    if unknown:
        raise HTTPException(
            status_code=422,
            detail={"code": "unknown_dimensions", "message": f"未知维度: {', '.join(sorted(unknown))}"},
        )

    total = sum(req.weights.values())
    if total <= 0:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_total", "message": "权重总和必须大于 0"},
        )

    normalized = {d: round(req.weights[d] / total * 100, 1) for d in DIMENSIONS}

    saved = calibrator._upsert_weights(req.user_id, req.platform, normalized, 0)
    return {
        "status": "manual_override",
        "user_id": req.user_id,
        "platform": req.platform,
        "weights": saved,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/calibrate/status
# ---------------------------------------------------------------------------

@router.get("/status", summary="获取校准状态")
async def get_calibration_status(
    user_id: str = Query(..., description="用户 ID"),
    platform: str = Query(..., description="平台名称"),
):
    """获取指定用户在某平台的 Fire Score 校准状态。

    返回：
    - 当前权重 vs 默认权重对比
    - 样本数量与数据质量评估
    - 最后校准时间
    """
    report = calibrator.get_calibration_report(user_id, platform)

    return {
        "user_id": user_id,
        "platform": platform,
        "summary": report["summary"],
        "weights": {
            "current": report["weights"]["current"],
            "default": report["weights"]["default"],
            "deviations_pct": report["weights"]["deviations_pct"],
        },
        "correlations": report["correlations"],
        "strongest_dimension": report.get("strongest_dimension"),
        "weakest_dimension": report.get("weakest_dimension"),
        "recommendations": report.get("recommendations", []),
        "generated_at": report["generated_at"],
    }


@router.get("/history", summary="获取校准历史数据")
async def get_calibration_history(
    user_id: str = Query(..., description="用户 ID"),
    platform: str = Query(..., description="平台名称"),
    limit: int = Query(default=20, ge=1, le=100, description="返回条数上限"),
):
    """获取用户在某平台的历史发布数据，用于校准分析。"""
    rows = calibrator.get_history(user_id, platform, limit=limit)
    return {
        "user_id": user_id,
        "platform": platform,
        "count": len(rows),
        "records": rows,
    }


@router.get("/defaults", summary="获取默认权重")
async def get_default_weights():
    """返回 Fire Score 五维默认权重配置。"""
    return {
        "default_weights": DEFAULT_WEIGHTS,
        "dimensions": DIMENSIONS,
        "min_samples_required": MIN_SAMPLES,
    }
