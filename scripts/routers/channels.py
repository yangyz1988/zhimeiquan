"""内容分发渠道 API"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter()


def _get_user(request: Request) -> str:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401, detail="未授权")
    return uid


class CreateChannelRequest(BaseModel):
    name: str
    platform: str
    channel_type: str = "SOCIAL"
    account_name: str | None = None
    account_id: str | None = None
    config: dict | None = None
    daily_limit: int | None = None


class UpdateChannelRequest(BaseModel):
    name: str | None = None
    config: dict | None = None
    daily_limit: int | None = None
    is_active: bool | None = None


@router.get("/")
async def list_channels(request: Request, platform: str | None = None):
    """列出用户的分发渠道"""
    _get_user(request)
    return {"channels": [], "total": 0}


@router.post("/")
async def create_channel(request: Request, req: CreateChannelRequest):
    """创建分发渠道"""
    _get_user(request)
    return {"id": "new", "name": req.name, "platform": req.platform}


@router.get("/{channel_id}")
async def get_channel(request: Request, channel_id: str):
    """获取单个渠道详情"""
    _get_user(request)
    return {"id": channel_id}


@router.patch("/{channel_id}")
async def update_channel(request: Request, channel_id: str, req: UpdateChannelRequest):
    """更新渠道配置"""
    _get_user(request)
    return {"id": channel_id, "updated": True}


@router.delete("/{channel_id}")
async def delete_channel(request: Request, channel_id: str):
    """删除渠道"""
    _get_user(request)
    return {"success": True}


@router.get("/{channel_id}/metrics")
async def get_channel_metrics(
    request: Request,
    channel_id: str,
    days: int = 30,
):
    """获取渠道表现指标"""
    _get_user(request)
    return {
        "channel_id": channel_id,
        "followers": 0,
        "engagement": 0.0,
        "trend": [],
    }
