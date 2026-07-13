"""标签体系 API — 接入真实数据库"""

from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel
from services.database import get_db, generate_id
from services.logging import logger
from datetime import datetime
import json

router = APIRouter()


def _get_user(request: Request) -> str:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401, detail="未授权")
    return uid


def _slugify(name: str) -> str:
    """生成 slug"""
    import re
    slug = re.sub(r'[^\w\u4e00-\u9fff-]', '-', name.lower())
    return re.sub(r'-+', '-', slug).strip('-')


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
    db = get_db()

    sql = "SELECT * FROM tags"
    params = []
    conditions = []

    if group_id:
        conditions.append("group_id = ?")
        params.append(group_id)
    if q:
        conditions.append("name LIKE ?")
        params.append(f"%{q}%")

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += f" ORDER BY usage_count DESC, name ASC LIMIT {limit}"

    rows = db.conn.execute(sql, params).fetchall()
    tags = [dict(row) for row in rows]

    total = db.conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    return {"tags": tags, "total": total}


@router.post("/")
async def create_tag(request: Request, req: CreateTagRequest):
    """创建标签"""
    _get_user(request)
    db = get_db()
    tag_id = generate_id()
    now = datetime.utcnow().isoformat()
    slug = req.slug or _slugify(req.name)

    try:
        db.conn.execute("""
            INSERT INTO tags (id, name, slug, color, description, group_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [tag_id, req.name, slug, req.color, req.description, req.group_id, now, now])
        db.conn.commit()
    except Exception as e:
        if "UNIQUE" in str(e):
            raise HTTPException(status_code=400, detail="标签名或slug已存在")
        raise

    logger.info(f"标签创建: {tag_id} ({req.name})")
    return {"id": tag_id, "name": req.name, "slug": slug, "color": req.color}


@router.delete("/{tag_id}")
async def delete_tag(request: Request, tag_id: str):
    """删除标签"""
    _get_user(request)
    db = get_db()

    row = db.conn.execute("SELECT id, is_system FROM tags WHERE id = ?", [tag_id]).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="标签不存在")
    if row["is_system"]:
        raise HTTPException(status_code=400, detail="系统标签不可删除")

    db.conn.execute("DELETE FROM content_tags WHERE tag_id = ?", [tag_id])
    db.conn.execute("DELETE FROM tags WHERE id = ?", [tag_id])
    db.conn.commit()

    logger.info(f"标签删除: {tag_id}")
    return {"success": True}


# ── Tag Groups ──

@router.get("/groups")
async def list_tag_groups(request: Request):
    """列出标签分组"""
    _get_user(request)
    db = get_db()

    rows = db.conn.execute("""
        SELECT tg.*, COUNT(t.id) as tag_count
        FROM tag_groups tg
        LEFT JOIN tags t ON t.group_id = tg.id
        GROUP BY tg.id
        ORDER BY tg.sort_order, tg.name
    """).fetchall()

    groups = [dict(row) for row in rows]
    return {"groups": groups}


@router.post("/groups")
async def create_tag_group(request: Request, req: CreateTagGroupRequest):
    """创建标签分组"""
    _get_user(request)
    db = get_db()
    group_id = generate_id()
    now = datetime.utcnow().isoformat()
    slug = req.slug or _slugify(req.name)

    try:
        db.conn.execute("""
            INSERT INTO tag_groups (id, name, slug, color, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [group_id, req.name, slug, req.color, req.description, now, now])
        db.conn.commit()
    except Exception as e:
        if "UNIQUE" in str(e):
            raise HTTPException(status_code=400, detail="分组名或slug已存在")
        raise

    return {"id": group_id, "name": req.name, "slug": slug}


@router.delete("/groups/{group_id}")
async def delete_tag_group(request: Request, group_id: str):
    """删除标签分组（标签保留，group_id置空）"""
    _get_user(request)
    db = get_db()

    row = db.conn.execute("SELECT id FROM tag_groups WHERE id = ?", [group_id]).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="分组不存在")

    # 将该组下的标签的 group_id 置空
    db.conn.execute("UPDATE tags SET group_id = NULL WHERE group_id = ?", [group_id])
    db.conn.execute("DELETE FROM tag_groups WHERE id = ?", [group_id])
    db.conn.commit()

    return {"success": True}


# ── Entity Tagging ──

@router.post("/entity")
async def tag_entity(request: Request, req: TagEntityRequest):
    """给实体打标签"""
    _get_user(request)
    db = get_db()
    now = datetime.utcnow().isoformat()

    # 先清除实体的所有旧标签
    db.conn.execute(
        "DELETE FROM content_tags WHERE entity_type = ? AND entity_id = ?",
        [req.entity_type, req.entity_id]
    )

    # 添加新标签
    for tag_id in req.tag_ids:
        db.conn.execute("""
            INSERT OR IGNORE INTO content_tags (tag_id, entity_type, entity_id, created_at)
            VALUES (?, ?, ?, ?)
        """, [tag_id, req.entity_type, req.entity_id, now])

    # 更新标签使用计数
    for tag_id in req.tag_ids:
        db.conn.execute("""
            UPDATE tags SET usage_count = usage_count + 1, updated_at = ?
            WHERE id = ?
        """, [now, tag_id])

    db.conn.commit()

    return {"tagged": len(req.tag_ids), "entity_type": req.entity_type, "entity_id": req.entity_id}


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_tags(request: Request, entity_type: str, entity_id: str):
    """获取实体的标签列表"""
    _get_user(request)
    db = get_db()

    rows = db.conn.execute("""
        SELECT t.* FROM tags t
        JOIN content_tags ct ON ct.tag_id = t.id
        WHERE ct.entity_type = ? AND ct.entity_id = ?
        ORDER BY t.name
    """, [entity_type, entity_id]).fetchall()

    tags = [dict(row) for row in rows]
    return {"tags": tags, "entity_type": entity_type, "entity_id": entity_id}