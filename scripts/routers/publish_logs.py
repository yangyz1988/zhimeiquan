"""发布日志 API — 接入真实数据库"""

from fastapi import APIRouter, Request, HTTPException, Query
from services.database import get_db, generate_id
from services.logging import logger
from datetime import datetime

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
    user_id = _get_user(request)
    db = get_db()
    offset = (page - 1) * limit

    # 验证 channel_id 属于当前用户
    if channel_id:
        ch_row = db.conn.execute(
            "SELECT id FROM distribution_channels WHERE id = ? AND user_id = ?",
            [channel_id, user_id]
        ).fetchone()
        if not ch_row:
            raise HTTPException(status_code=404, detail="渠道不存在")

    sql = """
        SELECT pl.*, dc.name as channel_name, dc.platform
        FROM publish_logs pl
        JOIN distribution_channels dc ON dc.id = pl.channel_id
        WHERE dc.user_id = ?
    """
    params = [user_id]

    if channel_id:
        sql += " AND pl.channel_id = ?"
        params.append(channel_id)
    if status:
        sql += " AND pl.status = ?"
        params.append(status)

    sql += " ORDER BY pl.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = db.conn.execute(sql, params).fetchall()
    logs = [dict(row) for row in rows]

    # 计算总数
    count_sql = """
        SELECT COUNT(*) FROM publish_logs pl
        JOIN distribution_channels dc ON dc.id = pl.channel_id
        WHERE dc.user_id = ?
    """
    count_params = [user_id]
    if channel_id:
        count_sql += " AND pl.channel_id = ?"
        count_params.append(channel_id)
    if status:
        count_sql += " AND pl.status = ?"
        count_params.append(status)

    total = db.conn.execute(count_sql, count_params).fetchone()[0]

    return {"logs": logs, "total": total, "page": page, "limit": limit}


@router.get("/{log_id}")
async def get_publish_log(request: Request, log_id: str):
    """获取单条发布日志"""
    user_id = _get_user(request)
    db = get_db()

    row = db.conn.execute("""
        SELECT pl.*, dc.name as channel_name, dc.platform
        FROM publish_logs pl
        JOIN distribution_channels dc ON dc.id = pl.channel_id
        WHERE pl.id = ? AND dc.user_id = ?
    """, [log_id, user_id]).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="日志不存在")

    return dict(row)


@router.post("/{log_id}/retry")
async def retry_publish(request: Request, log_id: str):
    """重试失败发布"""
    user_id = _get_user(request)
    db = get_db()

    row = db.conn.execute("""
        SELECT pl.*, dc.user_id
        FROM publish_logs pl
        JOIN distribution_channels dc ON dc.id = pl.channel_id
        WHERE pl.id = ?
    """, [log_id]).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="日志不存在")
    if row["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="无权操作")
    if row["status"] not in ("FAILED", "TIMEOUT"):
        raise HTTPException(status_code=400, detail="只能重试失败的任务")

    # 重置状态
    now = datetime.utcnow().isoformat()
    db.conn.execute("""
        UPDATE publish_logs
        SET status = 'PENDING', retry_count = retry_count + 1,
            error_message = NULL, updated_at = ?
        WHERE id = ?
    """, [now, log_id])
    db.conn.commit()

    logger.info(f"发布重试: {log_id}")
    return {"id": log_id, "status": "PENDING", "message": "已加入重试队列"}


@router.delete("/{log_id}")
async def cancel_publish(request: Request, log_id: str):
    """取消待发布任务"""
    user_id = _get_user(request)
    db = get_db()

    row = db.conn.execute("""
        SELECT pl.*, dc.user_id
        FROM publish_logs pl
        JOIN distribution_channels dc ON dc.id = pl.channel_id
        WHERE pl.id = ?
    """, [log_id]).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="日志不存在")
    if row["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="无权操作")
    if row["status"] != "PENDING":
        raise HTTPException(status_code=400, detail="只能取消待发布的任务")

    db.conn.execute("DELETE FROM publish_logs WHERE id = ?", [log_id])
    db.conn.commit()

    return {"success": True, "message": "已取消"}