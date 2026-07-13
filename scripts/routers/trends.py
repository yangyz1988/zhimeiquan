"""热点事件追踪 API — 接入真实数据库"""

from fastapi import APIRouter, Request, HTTPException, Query
from services.database import get_db, generate_id
from services.logging import logger
from datetime import datetime, timedelta
import json

router = APIRouter()


def _get_user(request: Request) -> str:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401, detail="未授权")
    return uid


@router.get("/")
async def list_trends(
    request: Request,
    platform: str | None = Query(None),
    category: str | None = Query(None),
    trend: str | None = Query(None),
    min_score: float = Query(0, ge=0, le=100),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """列出热点事件"""
    _get_user(request)
    db = get_db()
    offset = (page - 1) * limit

    sql = "SELECT * FROM trend_events WHERE is_active = 1 AND heat_score >= ?"
    params = [min_score]

    if platform:
        sql += " AND source_platform = ?"
        params.append(platform)
    if category:
        sql += " AND category = ?"
        params.append(category)
    if trend:
        sql += " AND heat_trend = ?"
        params.append(trend)

    sql += " ORDER BY heat_score DESC, last_seen_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = db.conn.execute(sql, params).fetchall()
    events = []
    for row in rows:
        ev = dict(row)
        if ev.get("keywords"):
            ev["keywords"] = json.loads(ev["keywords"])
        if ev.get("related_events"):
            ev["related_events"] = json.loads(ev["related_events"])
        if ev.get("content_suggestions"):
            ev["content_suggestions"] = json.loads(ev["content_suggestions"])
        events.append(ev)

    total = db.conn.execute(
        "SELECT COUNT(*) FROM trend_events WHERE is_active = 1"
    ).fetchone()[0]

    return {"events": events, "total": total, "page": page, "limit": limit}


@router.get("/{event_id}")
async def get_trend(request: Request, event_id: str):
    """获取单个热点事件详情"""
    _get_user(request)
    db = get_db()

    row = db.conn.execute(
        "SELECT * FROM trend_events WHERE id = ?", [event_id]
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="事件不存在")

    ev = dict(row)
    if ev.get("keywords"):
        ev["keywords"] = json.loads(ev["keywords"])
    if ev.get("related_events"):
        ev["related_events"] = json.loads(ev["related_events"])
    if ev.get("content_suggestions"):
        ev["content_suggestions"] = json.loads(ev["content_suggestions"])

    # 获取快照
    snap_rows = db.conn.execute("""
        SELECT * FROM trend_snapshots
        WHERE event_id = ?
        ORDER BY recorded_at DESC
        LIMIT 168
    """, [event_id]).fetchall()

    ev["snapshots"] = []
    for sr in snap_rows:
        snap = dict(sr)
        if snap.get("top_keywords"):
            snap["top_keywords"] = json.loads(snap["top_keywords"])
        if snap.get("source_breakdown"):
            snap["source_breakdown"] = json.loads(snap["source_breakdown"])
        ev["snapshots"].append(snap)

    return ev


@router.get("/{event_id}/snapshots")
async def get_trend_snapshots(
    request: Request,
    event_id: str,
    hours: int = Query(24, ge=1, le=168),
):
    """获取事件的历史热度快照"""
    _get_user(request)
    db = get_db()
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    rows = db.conn.execute("""
        SELECT * FROM trend_snapshots
        WHERE event_id = ? AND recorded_at >= ?
        ORDER BY recorded_at ASC
    """, [event_id, since]).fetchall()

    snapshots = []
    for row in rows:
        snap = dict(row)
        if snap.get("top_keywords"):
            snap["top_keywords"] = json.loads(snap["top_keywords"])
        snapshots.append(snap)

    return {
        "event_id": event_id,
        "snapshots": snapshots,
        "hours": hours,
        "count": len(snapshots)
    }


@router.post("/scan")
async def trigger_trend_scan(request: Request):
    """手动触发全平台热点扫描"""
    user_id = _get_user(request)
    db = get_db()

    # 这里应该调用实际的扫描服务
    # 目前只返回模拟结果
    logger.info(f"热点扫描触发: by {user_id}")

    # 模拟创建一个热点事件
    now = datetime.utcnow()
    event_id = generate_id()

    db.conn.execute("""
        INSERT INTO trend_events (
            id, title, summary, source_platform, category,
            heat_score, heat_trend, first_seen_at, last_seen_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        event_id, "示例热点", "这是一个示例热点事件", "抖音", "娱乐",
        75.5, "RISING", now.isoformat(), now.isoformat(), now.isoformat(), now.isoformat()
    ])
    db.conn.commit()

    return {"message": "扫描已触发", "new_events": 1, "event_id": event_id}


@router.get("/suggestions/{event_id}")
async def get_content_suggestions(request: Request, event_id: str):
    """获取基于热点的内容创作建议"""
    _get_user(request)
    db = get_db()

    row = db.conn.execute(
        "SELECT * FROM trend_events WHERE id = ?", [event_id]
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="事件不存在")

    ev = dict(row)
    keywords = json.loads(ev.get("keywords") or "[]")

    # 简单的内容建议生成
    angles = [
        f"从{keywords[0] if keywords else '热点'}角度解读",
        "用户痛点分析",
        "行业影响深度剖析",
        "争议观点对比",
        "数据可视化解读",
    ]

    return {
        "event_id": event_id,
        "title": ev["title"],
        "angles": angles,
        "keywords": keywords,
        "estimated_potential": "中" if ev["heat_score"] < 70 else "高",
        "platform_suggestions": {
            "抖音": {"format": "短视频", "duration": "15-60秒"},
            "小红书": {"format": "图文", "images": "6-9张"},
            "B站": {"format": "中视频", "duration": "5-15分钟"},
        }
    }