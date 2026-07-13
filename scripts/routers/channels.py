"""内容分发渠道 API — 接入真实数据库"""

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
async def list_channels(request: Request, platform: str | None = Query(None)):
    """列出用户的分发渠道"""
    user_id = _get_user(request)
    db = get_db()

    sql = "SELECT * FROM distribution_channels WHERE user_id = ?"
    params = [user_id]

    if platform:
        sql += " AND platform = ?"
        params.append(platform)

    sql += " ORDER BY created_at DESC"

    rows = db.conn.execute(sql, params).fetchall()
    channels = []
    for row in rows:
        ch = dict(row)
        if ch.get("config"):
            ch["config"] = json.loads(ch["config"])
        if ch.get("metrics"):
            ch["metrics"] = json.loads(ch["metrics"])
        channels.append(ch)

    return {"channels": channels, "total": len(channels)}


@router.post("/")
async def create_channel(request: Request, req: CreateChannelRequest):
    """创建分发渠道"""
    user_id = _get_user(request)
    db = get_db()
    channel_id = generate_id()
    now = datetime.utcnow().isoformat()

    try:
        db.conn.execute("""
            INSERT INTO distribution_channels (
                id, user_id, name, platform, channel_type, account_name, account_id,
                config, daily_limit, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            channel_id, user_id, req.name, req.platform, req.channel_type,
            req.account_name, req.account_id,
            json.dumps(req.config or {}),
            req.daily_limit,
            now, now
        ])
        db.conn.commit()
    except Exception as e:
        if "UNIQUE" in str(e):
            raise HTTPException(status_code=400, detail="该平台账号已添加")
        raise

    logger.info(f"渠道创建: {channel_id} ({req.platform}/{req.account_name})")
    return {
        "id": channel_id,
        "name": req.name,
        "platform": req.platform,
        "channel_type": req.channel_type,
        "created_at": now
    }


@router.get("/{channel_id}")
async def get_channel(request: Request, channel_id: str):
    """获取单个渠道详情"""
    user_id = _get_user(request)
    db = get_db()

    row = db.conn.execute(
        "SELECT * FROM distribution_channels WHERE id = ? AND user_id = ?",
        [channel_id, user_id]
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="渠道不存在")

    ch = dict(row)
    if ch.get("config"):
        ch["config"] = json.loads(ch["config"])
    if ch.get("metrics"):
        ch["metrics"] = json.loads(ch["metrics"])
    return ch


@router.patch("/{channel_id}")
async def update_channel(request: Request, channel_id: str, req: UpdateChannelRequest):
    """更新渠道配置"""
    user_id = _get_user(request)
    db = get_db()

    row = db.conn.execute(
        "SELECT id FROM distribution_channels WHERE id = ? AND user_id = ?",
        [channel_id, user_id]
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="渠道不存在")

    fields = []
    values = []
    if req.name is not None:
        fields.append("name = ?")
        values.append(req.name)
    if req.config is not None:
        fields.append("config = ?")
        values.append(json.dumps(req.config))
    if req.daily_limit is not None:
        fields.append("daily_limit = ?")
        values.append(req.daily_limit)
    if req.is_active is not None:
        fields.append("is_active = ?")
        values.append(1 if req.is_active else 0)

    if not fields:
        return {"id": channel_id, "message": "无更新"}

    fields.append("updated_at = ?")
    values.append(datetime.utcnow().isoformat())
    values.append(channel_id)

    db.conn.execute(
        f"UPDATE distribution_channels SET {', '.join(fields)} WHERE id = ?", values
    )
    db.conn.commit()

    return {"id": channel_id, "updated": True}


@router.delete("/{channel_id}")
async def delete_channel(request: Request, channel_id: str):
    """删除渠道"""
    user_id = _get_user(request)
    db = get_db()

    row = db.conn.execute(
        "SELECT id FROM distribution_channels WHERE id = ? AND user_id = ?",
        [channel_id, user_id]
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="渠道不存在")

    # CASCADE 会自动删除 publish_logs 和 channel_metrics
    db.conn.execute("DELETE FROM distribution_channels WHERE id = ?", [channel_id])
    db.conn.commit()

    logger.info(f"渠道删除: {channel_id} by {user_id}")
    return {"success": True}


@router.get("/{channel_id}/metrics")
async def get_channel_metrics(
    request: Request,
    channel_id: str,
    days: int = Query(30, ge=1, le=365),
):
    """获取渠道表现指标"""
    user_id = _get_user(request)
    db = get_db()

    # 验证渠道所有权
    row = db.conn.execute(
        "SELECT id FROM distribution_channels WHERE id = ? AND user_id = ?",
        [channel_id, user_id]
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="渠道不存在")

    # 获取最近 N 天的指标
    rows = db.conn.execute("""
        SELECT * FROM channel_metrics
        WHERE channel_id = ?
        ORDER BY collected_at DESC
        LIMIT ?
    """, [channel_id, days]).fetchall()

    metrics = [dict(row) for row in rows]
    if metrics and metrics[0].get("top_performing"):
        metrics[0]["top_performing"] = json.loads(metrics[0]["top_performing"])

    # 计算趋势
    if len(metrics) >= 2:
        latest = metrics[0]
        prev = metrics[-1]
        trend = {
            "followers_change": latest["followers"] - prev["followers"],
            "engagement_change": round(latest["engagement"] - prev["engagement"], 4),
        }
    else:
        trend = {"followers_change": 0, "engagement_change": 0.0}

    return {
        "channel_id": channel_id,
        "followers": metrics[0]["followers"] if metrics else 0,
        "engagement": metrics[0]["engagement"] if metrics else 0.0,
        "trend": trend,
        "history": metrics,
    }