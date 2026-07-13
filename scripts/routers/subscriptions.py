"""订阅管理 API — 接入真实数据库"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
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


PLAN_FEATURES = {
    "FREE": {"credits": 100, "api_calls": 1000, "storage_gb": 1},
    "PRO": {"credits": 1000, "api_calls": 10000, "storage_gb": 10},
    "TEAM": {"credits": 5000, "api_calls": 50000, "storage_gb": 50},
    "ENTERPRISE": {"credits": 50000, "api_calls": 500000, "storage_gb": 500},
}


@router.get("/")
async def get_subscription(request: Request):
    """获取当前用户的订阅信息"""
    user_id = _get_user(request)
    db = get_db()

    row = db.conn.execute(
        "SELECT * FROM subscriptions WHERE user_id = ?", [user_id]
    ).fetchone()

    if not row:
        # 创建默认免费订阅
        now = datetime.utcnow()
        sub_id = generate_id()
        db.conn.execute("""
            INSERT INTO subscriptions (id, user_id, status, plan_tier, created_at, updated_at)
            VALUES (?, ?, 'ACTIVE', 'FREE', ?, ?)
        """, [sub_id, user_id, now.isoformat(), now.isoformat()])
        db.conn.commit()

        return {
            "id": sub_id,
            "plan": "FREE",
            "status": "ACTIVE",
            "current_period_end": None,
            "features": PLAN_FEATURES["FREE"],
        }

    sub = dict(row)
    sub["plan"] = sub.pop("plan_tier")
    sub["features"] = PLAN_FEATURES.get(sub["plan"], PLAN_FEATURES["FREE"])
    return sub


@router.post("/upgrade")
async def upgrade_subscription(request: Request, req: dict):
    """升级订阅计划"""
    user_id = _get_user(request)
    plan = req.get("plan", "PRO")
    if plan not in PLAN_FEATURES:
        raise HTTPException(status_code=400, detail="无效的计划")

    db = get_db()
    now = datetime.utcnow()
    period_end = now + timedelta(days=30)

    row = db.conn.execute(
        "SELECT id FROM subscriptions WHERE user_id = ?", [user_id]
    ).fetchone()

    if row:
        db.conn.execute("""
            UPDATE subscriptions
            SET plan_tier = ?, current_period_start = ?, current_period_end = ?,
                status = 'ACTIVE', updated_at = ?
            WHERE user_id = ?
        """, [plan, now.isoformat(), period_end.isoformat(), now.isoformat(), user_id])
    else:
        sub_id = generate_id()
        db.conn.execute("""
            INSERT INTO subscriptions (id, user_id, status, plan_tier, current_period_start, current_period_end, created_at, updated_at)
            VALUES (?, ?, 'ACTIVE', ?, ?, ?, ?, ?)
        """, [sub_id, user_id, plan, now.isoformat(), period_end.isoformat(), now.isoformat(), now.isoformat()])

    db.conn.commit()
    logger.info(f"订阅升级: {user_id} -> {plan}")
    return {"message": "升级成功", "plan": plan, "period_end": period_end.isoformat()}


@router.post("/cancel")
async def cancel_subscription(request: Request):
    """取消自动续费"""
    user_id = _get_user(request)
    db = get_db()
    now = datetime.utcnow()

    db.conn.execute("""
        UPDATE subscriptions
        SET cancel_at_period_end = 1, canceled_at = ?, updated_at = ?
        WHERE user_id = ?
    """, [now.isoformat(), now.isoformat(), user_id])
    db.conn.commit()

    return {"canceled": True, "message": "将在当前周期结束后取消"}


@router.post("/resume")
async def resume_subscription(request: Request):
    """恢复自动续费"""
    user_id = _get_user(request)
    db = get_db()
    now = datetime.utcnow()

    db.conn.execute("""
        UPDATE subscriptions
        SET cancel_at_period_end = 0, canceled_at = NULL, updated_at = ?
        WHERE user_id = ?
    """, [now.isoformat(), user_id])
    db.conn.commit()

    return {"resumed": True}


@router.get("/invoices")
async def list_invoices(request: Request, page: int = 1, limit: int = 20):
    """列出历史发票"""
    user_id = _get_user(request)
    db = get_db()
    offset = (page - 1) * limit

    rows = db.conn.execute("""
        SELECT i.* FROM invoices i
        JOIN subscriptions s ON s.id = i.subscription_id
        WHERE s.user_id = ?
        ORDER BY i.created_at DESC
        LIMIT ? OFFSET ?
    """, [user_id, limit, offset]).fetchall()

    total = db.conn.execute("""
        SELECT COUNT(*) FROM invoices i
        JOIN subscriptions s ON s.id = i.subscription_id
        WHERE s.user_id = ?
    """, [user_id]).fetchone()[0]

    invoices = [dict(row) for row in rows]
    return {"invoices": invoices, "total": total, "page": page}


@router.get("/billing")
async def get_billing_cycle(request: Request):
    """获取当前计费周期用量"""
    user_id = _get_user(request)
    db = get_db()
    now = datetime.utcnow()

    # 获取当前订阅
    sub_row = db.conn.execute(
        "SELECT * FROM subscriptions WHERE user_id = ?", [user_id]
    ).fetchone()

    if not sub_row:
        return {
            "cycle_start": None, "cycle_end": None,
            "credits_used": 0, "credits_limit": 100,
            "api_calls": 0, "api_calls_limit": 1000,
        }

    sub = dict(sub_row)
    features = PLAN_FEATURES.get(sub["plan_tier"], PLAN_FEATURES["FREE"])

    # 查找当前周期的用量
    cycle_row = db.conn.execute("""
        SELECT * FROM billing_cycles
        WHERE user_id = ? AND cycle_end >= ?
        ORDER BY cycle_start DESC LIMIT 1
    """, [user_id, now.isoformat()]).fetchone()

    if cycle_row:
        cycle = dict(cycle_row)
    else:
        cycle = {
            "cycle_start": sub.get("current_period_start"),
            "cycle_end": sub.get("current_period_end"),
            "credits_used": 0,
            "credits_limit": features["credits"],
            "api_calls": 0,
            "api_calls_limit": features["api_calls"],
        }

    return cycle