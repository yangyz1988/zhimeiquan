"""协作评论 API"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter()


def _get_user(request: Request) -> str:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401, detail="未授权")
    return uid


class CreateCommentRequest(BaseModel):
    body: str
    entity_type: str
    entity_id: str
    parent_id: str | None = None


class UpdateCommentRequest(BaseModel):
    body: str | None = None
    is_resolved: bool | None = None


@router.get("/{entity_type}/{entity_id}")
async def list_comments(
    request: Request,
    entity_type: str,
    entity_id: str,
    page: int = 1,
    limit: int = 50,
):
    """获取指定实体的评论列表"""
    _get_user(request)
    return {"comments": [], "total": 0, "page": page, "limit": limit}


@router.post("/")
async def create_comment(request: Request, req: CreateCommentRequest):
    """创建评论"""
    _get_user(request)
    return {"id": "new", "body": req.body, "entity_type": req.entity_type}


@router.patch("/{comment_id}")
async def update_comment(request: Request, comment_id: str, req: UpdateCommentRequest):
    """更新评论（编辑/标记已解决）"""
    _get_user(request)
    return {"id": comment_id, "updated": True}


@router.delete("/{comment_id}")
async def delete_comment(request: Request, comment_id: str):
    """删除评论"""
    _get_user(request)
    return {"success": True}
