"""协作评论 API — 接入真实数据库"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from services.database import get_db, generate_id
from services.logging import logger
from datetime import datetime

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
    """获取指定实体的评论列表（支持嵌套）"""
    user_id = _get_user(request)
    db = get_db()
    offset = (page - 1) * limit

    # 只返回顶层评论（parent_id 为空）
    rows = db.conn.execute("""
        SELECT * FROM comments
        WHERE entity_type = ? AND entity_id = ? AND parent_id IS NULL
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, [entity_type, entity_id, limit, offset]).fetchall()

    total = db.conn.execute(
        "SELECT COUNT(*) FROM comments WHERE entity_type = ? AND entity_id = ? AND parent_id IS NULL",
        [entity_type, entity_id]
    ).fetchone()[0]

    comments = [dict(row) for row in rows]

    # 获取每个顶层评论的子评论
    for c in comments:
        child_rows = db.conn.execute("""
            SELECT * FROM comments WHERE parent_id = ? ORDER BY created_at ASC
        """, [c["id"]]).fetchall()
        c["children"] = [dict(r) for r in child_rows]

    return {"comments": comments, "total": total, "page": page, "limit": limit}


@router.post("/")
async def create_comment(request: Request, req: CreateCommentRequest):
    """创建评论"""
    user_id = _get_user(request)
    db = get_db()
    comment_id = generate_id()
    now = datetime.utcnow().isoformat()

    db.conn.execute("""
        INSERT INTO comments (id, user_id, body, entity_type, entity_id, parent_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [comment_id, user_id, req.body, req.entity_type, req.entity_id, req.parent_id, now, now])
    db.conn.commit()

    logger.info(f"评论创建: {comment_id} on {req.entity_type}/{req.entity_id}")
    return {
        "id": comment_id,
        "body": req.body,
        "entity_type": req.entity_type,
        "entity_id": req.entity_id,
        "parent_id": req.parent_id,
        "is_resolved": False,
        "created_at": now
    }


@router.patch("/{comment_id}")
async def update_comment(request: Request, comment_id: str, req: UpdateCommentRequest):
    """更新评论（编辑/标记已解决）"""
    user_id = _get_user(request)
    db = get_db()

    row = db.conn.execute(
        "SELECT id, user_id FROM comments WHERE id = ?", [comment_id]
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="评论不存在")

    # 只有评论作者可以编辑，任何人可以标记解决
    if req.body is not None and row["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="只能编辑自己的评论")

    fields = []
    values = []
    if req.body is not None:
        fields.append("body = ?")
        values.append(req.body)
    if req.is_resolved is not None:
        fields.append("is_resolved = ?")
        values.append(1 if req.is_resolved else 0)

    if not fields:
        return {"id": comment_id, "message": "无更新"}

    fields.append("updated_at = ?")
    values.append(datetime.utcnow().isoformat())
    values.append(comment_id)

    db.conn.execute(
        f"UPDATE comments SET {', '.join(fields)} WHERE id = ?", values
    )
    db.conn.commit()

    return {"id": comment_id, "updated": True}


@router.delete("/{comment_id}")
async def delete_comment(request: Request, comment_id: str):
    """删除评论（同时删除子评论）"""
    user_id = _get_user(request)
    db = get_db()

    row = db.conn.execute(
        "SELECT id, user_id FROM comments WHERE id = ?", [comment_id]
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="评论不存在")

    if row["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="只能删除自己的评论")

    # CASCADE 会自动删除子评论
    db.conn.execute("DELETE FROM comments WHERE id = ?", [comment_id])
    db.conn.commit()

    logger.info(f"评论删除: {comment_id} by {user_id}")
    return {"success": True}