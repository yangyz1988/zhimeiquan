"""发布日志 API"""

from fastapi import APIRouter, Request, HTTPException, Query

router = APIRouter()


def _get_user(request: Request) -> str:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401, detail="未授权")
    return uid


@router.get("/")
async def list_publish_logs(
    request: Request,
    channel_id: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """列出发布日志"""
    _get_user(request)
    return {"logs": [], "total": 0, "page": page, "limit": limit}


@router.get("/{log_id}")
async def get_publish_log(request: Request, log_id: str):
    """获取单条发布日志"""
    _get_user(request)
    return {"id": log_id}


@router.post("/{log_id}/retry")
async def retry_publish(request: Request, log_id: str):
    """重试失败发布"""
    _get_user(request)
    return {"id": log_id, "status": "PENDING"}


@router.delete("/{log_id}")
async def cancel_publish(request: Request, log_id: str):
    """取消待发布任务"""
    _get_user(request)
    return {"success": True}
