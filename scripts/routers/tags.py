"""标签体系 API"""

from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


def _get_user(request: Request) -> str:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401, detail="未授权")
    return uid


class CreateTagRequest(BaseModel):
    name: str
    slug: str | None = None
    color: str | None = None
    description: str | None = None
    group_id: str | None = None


class CreateTagGroupRequest(BaseModel):
    name: str
    slug: str | None = None
    color: str | None = None
    description: str | None = None


class TagEntityRequest(BaseModel):
    tag_ids: list[str]
    entity_type: str
    entity_id: str


# ── Tags ──

@router.get("/")
async def list_tags(
    request: Request,
    group_id: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(50, le=200),
):
    """列出所有标签"""
    _get_user(request)
    return {"tags": [], "total": 0}


@router.post("/")
async def create_tag(request: Request, req: CreateTagRequest):
    """创建标签"""
    _get_user(request)
    return {"id": "new", "name": req.name, "slug": req.slug or req.name}


@router.delete("/{tag_id}")
async def delete_tag(request: Request, tag_id: str):
    """删除标签"""
    _get_user(request)
    return {"success": True}


# ── Tag Groups ──

@router.get("/groups")
async def list_tag_groups(request: Request):
    """列出标签分组"""
    _get_user(request)
    return {"groups": []}


@router.post("/groups")
async def create_tag_group(request: Request, req: CreateTagGroupRequest):
    """创建标签分组"""
    _get_user(request)
    return {"id": "new", "name": req.name}


@router.delete("/groups/{group_id}")
async def delete_tag_group(request: Request, group_id: str):
    """删除标签分组"""
    _get_user(request)
    return {"success": True}


# ── Entity Tagging ──

@router.post("/entity")
async def tag_entity(request: Request, req: TagEntityRequest):
    """给实体打标签"""
    _get_user(request)
    return {"tagged": len(req.tag_ids)}


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_tags(request: Request, entity_type: str, entity_id: str):
    """获取实体的标签列表"""
    _get_user(request)
    return {"tags": []}
