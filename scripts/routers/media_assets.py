"""媒体资产管理 API"""

from fastapi import APIRouter, Request, HTTPException, Query

router = APIRouter()


def _get_user(request: Request) -> str:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401, detail="未授权")
    return uid


@router.get("/list")
async def list_assets(
    request: Request,
    folder: str | None = Query(None),
    mime_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """列出用户的媒体资产"""
    _get_user(request)
    return {"assets": [], "total": 0, "page": page, "limit": limit}


@router.get("/{asset_id}")
async def get_asset(request: Request, asset_id: str):
    """获取单个媒体资产详情"""
    _get_user(request)
    return {"id": asset_id}


@router.post("/upload")
async def upload_asset(request: Request):
    """上传媒体文件"""
    _get_user(request)
    return {"message": "上传成功"}


@router.delete("/{asset_id}")
async def delete_asset(request: Request, asset_id: str):
    """删除媒体资产"""
    _get_user(request)
    return {"success": True}
