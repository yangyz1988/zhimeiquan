"""订阅管理 API"""

from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


def _get_user(request: Request) -> str:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401, detail="未授权")
    return uid


@router.get("/")
async def get_subscription(request: Request):
    """获取当前用户的订阅信息"""
    _get_user(request)
    return {
        "plan": "FREE",
        "status": "active",
        "current_period_end": None,
        "features": {},
    }


@router.post("/upgrade")
async def upgrade_subscription(request: Request):
    """升级订阅计划"""
    _get_user(request)
    return {"checkout_url": "https://stripe.com/..."}


@router.post("/cancel")
async def cancel_subscription(request: Request):
    """取消自动续费"""
    _get_user(request)
    return {"canceled": True, "message": "将在当前周期结束后取消"}


@router.post("/resume")
async def resume_subscription(request: Request):
    """恢复自动续费"""
    _get_user(request)
    return {"resumed": True}


@router.get("/invoices")
async def list_invoices(request: Request, page: int = 1, limit: int = 20):
    """列出历史发票"""
    _get_user(request)
    return {"invoices": [], "total": 0, "page": page}


@router.get("/billing")
async def get_billing_cycle(request: Request):
    """获取当前计费周期用量"""
    _get_user(request)
    return {
        "cycle_start": None,
        "cycle_end": None,
        "credits_used": 0,
        "credits_limit": 1000,
        "api_calls": 0,
        "api_calls_limit": 10000,
    }
