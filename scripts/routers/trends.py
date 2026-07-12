"""热点事件追踪 API"""

from fastapi import APIRouter, Request, HTTPException, Query

router = APIRouter()


def _get_user(request: Request) -> str:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401, detail="未授权")
    return uid


@router.get("/")
async def list_trends(
    request: Request,
    platform: str | None = Query(None),
    category: str | None = Query(None),
    trend: str | None = Query(None),  # RISING, STABLE, PEAKING, DECLINING
    min_score: float = Query(0, ge=0, le=100),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """列出热点事件"""
    _get_user(request)
    return {"events": [], "total": 0, "page": page, "limit": limit}


@router.get("/{event_id}")
async def get_trend(request: Request, event_id: str):
    """获取单个热点事件详情 + 历史快照"""
    _get_user(request)
    return {"id": event_id, "snapshots": []}


@router.get("/{event_id}/snapshots")
async def get_trend_snapshots(
    request: Request,
    event_id: str,
    hours: int = Query(24, ge=1, le=168),
):
    """获取事件的历史热度快照"""
    _get_user(request)
    return {
        "event_id": event_id,
        "snapshots": [],
        "hours": hours,
    }


@router.post("/scan")
async def trigger_trend_scan(request: Request):
    """手动触发全平台热点扫描"""
    _get_user(request)
    return {"message": "扫描已触发", "new_events": 0}


@router.get("/suggestions/{event_id}")
async def get_content_suggestions(request: Request, event_id: str):
    """获取基于热点的内容创作建议"""
    _get_user(request)
    return {
        "event_id": event_id,
        "angles": [],
        "keywords": [],
        "estimated_potential": "中",
    }
