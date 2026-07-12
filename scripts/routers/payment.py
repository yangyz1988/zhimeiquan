"""支付路由 - Stripe Checkout + Webhook"""

import os

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from services.logging import logger
from services.payment import PaymentService

router = APIRouter()
payment_service = PaymentService()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


class SubscribeRequest(BaseModel):
    user_id: str = Field(..., description="用户 ID（Clerk userId）")
    plan: str = Field(..., description="套餐标识: basic / pro / enterprise")
    success_url: str | None = Field(None, description="支付成功后跳转 URL")
    cancel_url: str | None = Field(None, description="取消支付后跳转 URL")


class SubscribeResponse(BaseModel):
    session_id: str
    url: str


@router.post("/subscribe")
async def subscribe(request: Request, body: SubscribeRequest):
    """
    创建 Stripe Checkout 订阅会话

    返回 session_id 和 Stripe Checkout URL，
    前端将用户重定向到该 URL 完成支付。
    """
    # 从 request.state 获取认证用户 ID（由中间件注入）
    auth_user_id = getattr(request.state, "user_id", None)

    # 安全修复：生产环境必须使用认证用户
    ENV = os.getenv("ENV", "development")
    if ENV == "production":
        if not auth_user_id or auth_user_id == "dev_mock_user":
            raise HTTPException(status_code=401, detail="未授权，请先登录")
        user_id = auth_user_id
    else:
        # 开发环境：优先使用认证用户，否则使用请求体中的 user_id
        user_id = auth_user_id if auth_user_id and auth_user_id != "dev_mock_user" else body.user_id

    success_url = body.success_url or f"{FRONTEND_URL}/dashboard?checkout=success"
    cancel_url = body.cancel_url or f"{FRONTEND_URL}/pricing?checkout=canceled"

    result = payment_service.create_checkout_session(
        user_id=user_id,
        plan=body.plan,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "session_id": result["session_id"],
        "url": result["url"],
    }


@router.post("/webhook")
async def webhook(request: Request):
    """
    接收 Stripe Webhook 事件

    验证签名后处理订阅相关事件：
    - checkout.session.completed: 支付完成
    - customer.subscription.updated: 订阅状态更新
    - customer.subscription.deleted: 订阅取消
    """
    sig_header = request.headers.get("stripe-signature", "")

    if not sig_header:
        logger.warning("Webhook 请求缺少 stripe-signature 头")
        raise HTTPException(status_code=400, detail="缺少 stripe-signature 请求头")

    payload = await request.body()

    try:
        event = payment_service.verify_webhook(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if event is None:
        raise HTTPException(status_code=400, detail="Webhook 签名验证失败")

    event_type = event.type

    # checkout.session.completed — 订阅创建完成（修复：实际更新用户订阅）
    if event_type == "checkout.session.completed":
        session = event.data.object  # type: ignore[attr-defined]
        user_id = session.get("metadata", {}).get("user_id", "")
        plan = session.get("metadata", {}).get("plan", "")
        
        logger.info(
            "Checkout 会话完成",
            session_id=session.get("id"),
            user_id=user_id,
            plan=plan,
        )
        
        # 修复：实际更新用户订阅状态
        if user_id and plan:
            try:
                subscription_id = session.get("subscription")
                if subscription_id:
                    # 创建订阅记录
                    result = payment_service.handle_subscription_updated_from_checkout(
                        user_id=user_id,
                        plan=plan,
                        subscription_id=subscription_id,
                    )
                    return {
                        "received": True,
                        "type": event_type,
                        "processed": "error" not in result,
                        "result": result,
                    }
            except Exception as e:
                logger.error(f"处理 checkout 完成事件失败: {e}")
        
        return {
            "received": True,
            "type": event_type,
            "processed": True,
        }

    # customer.subscription.updated — 订阅状态更新
    if event_type == "customer.subscription.updated":
        result = payment_service.handle_subscription_updated(event)
        return {
            "received": True,
            "type": event_type,
            "processed": "error" not in result,
            "result": result,
        }

    # customer.subscription.deleted — 订阅被取消
    if event_type == "customer.subscription.deleted":
        subscription = event.data.object  # type: ignore[attr-defined]
        user_id = subscription.get("metadata", {}).get("user_id", "")
        logger.info(
            "订阅已取消",
            user_id=user_id,
            subscription_id=subscription.get("id"),
        )
        # 更新用户订阅状态为已取消
        if user_id:
            try:
                payment_service.cancel_user_subscription(user_id)
            except Exception as e:
                logger.error(f"取消用户订阅失败: {e}")
        
        return {
            "received": True,
            "type": event_type,
            "processed": True,
        }

    # 未处理的事件类型，仍然确认接收（防止 Stripe 重试）
    logger.info("收到未处理的 Stripe 事件", event_type=event_type)
    return {
        "received": True,
        "type": event_type,
        "processed": False,
        "message": f"事件类型 {event_type} 未配置处理逻辑",
    }
