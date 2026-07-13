"""媒体资产管理 API — 接入真实数据库"""

from fastapi import APIRouter, Request, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from services.database import get_db, generate_id
from services.logging import logger
import json
from datetime import datetime

router = APIRouter()


def _get_user(request: Request) -> str:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401, detail="未授权")
    return uid


class AssetCreate(BaseModel):
    file_name: str
    original_name: str | None = None
    mime_type: str
    size: int = 0
    url: str
    thumbnail_url: str | None = None
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    alt_text: str | None = None
    tags: list[str] | None = None
    folder: str | None = None
    is_public: bool = False
    metadata: dict | None = None


@router.get("/list")
async def list_assets(
    request: Request,
    folder: str | None = Query(None),
    mime_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """列出用户的媒体资产"""
    user_id = _get_user(request)
    db = get_db()
    offset = (page - 1) * limit

    sql = "SELECT * FROM media_assets WHERE user_id = ?"
    params = [user_id]

    if folder:
        sql += " AND folder = ?"
        params.append(folder)
    if mime_type:
        sql += " AND mime_type LIKE ?"
        params.append(f"{mime_type}%")

    sql += f" ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"

    rows = db.conn.execute(sql, params).fetchall()
    total = db.conn.execute(
        "SELECT COUNT(*) FROM media_assets WHERE user_id = ?", [user_id]
    ).fetchone()[0]

    assets = [dict(row) for row in rows]
    for a in assets:
        if a.get("tags"):
            a["tags"] = json.loads(a["tags"])
        if a.get("metadata"):
            a["metadata"] = json.loads(a["metadata"])

    return {"assets": assets, "total": total, "page": page, "limit": limit}


@router.get("/{asset_id}")
async def get_asset(request: Request, asset_id: str):
    """获取单个媒体资产详情"""
    user_id = _get_user(request)
    db = get_db()

    row = db.conn.execute(
        "SELECT * FROM media_assets WHERE id = ? AND user_id = ?",
        [asset_id, user_id]
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="资产不存在")

    asset = dict(row)
    if asset.get("tags"):
        asset["tags"] = json.loads(asset["tags"])
    if asset.get("metadata"):
        asset["metadata"] = json.loads(asset["metadata"])

    return asset


@router.post("/upload")
async def upload_asset(request: Request, req: AssetCreate):
    """上传媒体文件"""
    user_id = _get_user(request)
    db = get_db()
    asset_id = generate_id()
    now = datetime.utcnow().isoformat()

    db.conn.execute("""
        INSERT INTO media_assets (
            id, user_id, file_name, original_name, mime_type, size, url,
            thumbnail_url, width, height, duration, alt_text, tags, folder,
            is_public, metadata, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        asset_id, user_id, req.file_name, req.original_name, req.mime_type,
        req.size, req.url, req.thumbnail_url, req.width, req.height,
        req.duration, req.alt_text,
        json.dumps(req.tags or []),
        req.folder or "default",
        1 if req.is_public else 0,
        json.dumps(req.metadata or {}),
        now, now
    ])
    db.conn.commit()

    logger.info(f"媒体资产创建: {asset_id} by {user_id}")
    return {"id": asset_id, "message": "上传成功", "created_at": now}


@router.patch("/{asset_id}")
async def update_asset(request: Request, asset_id: str, updates: dict):
    """更新媒体资产"""
    user_id = _get_user(request)
    db = get_db()

    # 检查所有权
    row = db.conn.execute(
        "SELECT id FROM media_assets WHERE id = ? AND user_id = ?",
        [asset_id, user_id]
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="资产不存在")

    allowed = ["file_name", "alt_text", "tags", "folder", "is_public", "metadata"]
    fields = []
    values = []
    for k, v in updates.items():
        if k in allowed:
            fields.append(f"{k} = ?")
            if k in ("tags", "metadata"):
                values.append(json.dumps(v))
            elif k == "is_public":
                values.append(1 if v else 0)
            else:
                values.append(v)

    if not fields:
        return {"id": asset_id, "message": "无更新"}

    fields.append("updated_at = ?")
    values.append(datetime.utcnow().isoformat())
    values.append(asset_id)

    db.conn.execute(
        f"UPDATE media_assets SET {', '.join(fields)} WHERE id = ?",
        values
    )
    db.conn.commit()

    return {"id": asset_id, "updated": True}


@router.delete("/{asset_id}")
async def delete_asset(request: Request, asset_id: str):
    """删除媒体资产"""
    user_id = _get_user(request)
    db = get_db()

    row = db.conn.execute(
        "SELECT id FROM media_assets WHERE id = ? AND user_id = ?",
        [asset_id, user_id]
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="资产不存在")

    db.conn.execute("DELETE FROM media_assets WHERE id = ?", [asset_id])
    db.conn.commit()

    logger.info(f"媒体资产删除: {asset_id} by {user_id}")
    return {"success": True}