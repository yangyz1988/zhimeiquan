"""Stripe 支付集成

功能:
- 订阅创建/取消
- Webhook 处理
- 发票管理
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ========================================
# 配置
# ========================================

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_API_BASE = "https://api.stripe.com/v1"

# 价格映射
PRICE_IDS = {
    "PRO_MONTHLY": os.getenv("STRIPE_PRICE_PRO_MONTHLY", "price_pro_monthly"),
    "PRO_YEARLY": os.getenv("STRIPE_PRICE_PRO_YEARLY", "price_pro_yearly"),
    "TEAM_MONTHLY": os.getenv("STRIPE_PRICE_TEAM_MONTHLY", "price_team_monthly"),
    "TEAM_YEARLY": os.getenv("STRIPE_PRICE_TEAM_YEARLY", "price_team_yearly"),
    "ENTERPRISE_MONTHLY": os.getenv("STRIPE_PRICE_ENTERPRISE_MONTHLY", "price_enterprise_monthly"),
}

# ========================================
# 模型
# ========================================

class SubscriptionCreate(BaseModel):
    user_id: str
    plan: str
    billing_cycle: str = "monthly"
    success_url: str
    cancel_url: str


class SubscriptionUpdate(BaseModel):
    subscription_id: str
    new_plan: str


class InvoiceData(BaseModel):
    invoice_id: str
    amount: int
    currency: str
    status: str
    created_at: datetime


# ========================================
# Stripe API 客户端
# ========================================

class StripeClient:
    """Stripe API 客户端"""

    def __init__(self, api_key: str = STRIPE_SECRET_KEY):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """发送请求"""
        url = f"{STRIPE_API_BASE}/{endpoint}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                data=data or {}
            )
            response.raise_for_status()
            return response.json()

    async def create_customer(
        self,
        user_id: str,
        email: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建客户"""
        data = {
            "email": email,
            "metadata[user_id]": user_id,
        }
        if name:
            data["name"] = name
        return await self._request("POST", "customers", data)

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """创建结账会话"""
        data = {
            "customer": customer_id,
            "mode": "subscription",
            "line_items[0][price]": price_id,
            "line_items[0][quantity]": "1",
            "success_url": success_url,
            "cancel_url": cancel_url,
        }
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value
        return await self._request("POST", "checkout/sessions", data)

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """获取订阅"""
        return await self._request("GET", f"subscriptions/{subscription_id}")

    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> Dict[str, Any]:
        """取消订阅"""
        data = {}
        if at_period_end:
            data["cancel_at_period_end"] = "true"
        else:
            data["cancel_at"] = "now"
        return await self._request("POST", f"subscriptions/{subscription_id}/cancel", data)

    async def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """获取发票"""
        return await self._request("GET", f"invoices/{invoice_id}")

    async def list_invoices(
        self,
        customer_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """列出客户发票"""
        return await self._request(
            "GET",
            f"invoices?customer={customer_id}&limit={limit}"
        )


# ========================================
# 业务服务
# ========================================

class PaymentService:
    """支付服务"""

    def __init__(self):
        self.client = StripeClient()

    async def create_subscription(
        self,
        data: SubscriptionCreate,
        email: str,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建订阅"""
        # 获取或创建客户
        if not customer_id:
            customer = await self.client.create_customer(
                user_id=data.user_id,
                email=email
            )
            customer_id = customer["id"]

        # 获取价格 ID
        price_key = f"{data.plan}_{data.billing_cycle.upper()}"
        price_id = PRICE_IDS.get(price_key)
        if not price_id:
            raise ValueError(f"未找到价格配置: {price_key}")

        # 创建结账会话
        session = await self.client.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            metadata={"user_id": data.user_id, "plan": data.plan}
        )

        return {
            "checkout_url": session["url"],
            "session_id": session["id"],
            "customer_id": customer_id,
        }

    async def cancel_subscription(
        self,
        subscription_id: str,
        immediate: bool = False
    ) -> Dict[str, Any]:
        """取消订阅"""
        result = await self.client.cancel_subscription(
            subscription_id=subscription_id,
            at_period_end=not immediate
        )
        return {
            "subscription_id": result["id"],
            "status": result["status"],
            "cancel_at_period_end": result.get("cancel_at_period_end", False),
            "canceled_at": result.get("canceled_at"),
        }

    async def get_subscription_status(
        self,
        subscription_id: str
    ) -> Dict[str, Any]:
        """获取订阅状态"""
        sub = await self.client.get_subscription(subscription_id)
        return {
            "subscription_id": sub["id"],
            "status": sub["status"],
            "plan": sub["items"]["data"][0]["price"]["nickname"]
            if sub.get("items") else None,
            "current_period_end": sub.get("current_period_end"),
            "cancel_at_period_end": sub.get("cancel_at_period_end", False),
        }

    async def handle_webhook(
        self,
        payload: bytes,
        sig_header: str
    ) -> Dict[str, Any]:
        """处理 Webhook（需要验证签名）"""
        # 简化实现，生产环境需要验证签名
        import json
        event = json.loads(payload)

        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        result = {
            "event_type": event_type,
            "processed": False,
        }

        # 处理不同事件
        if event_type == "checkout.session.completed":
            # 订阅成功
            result["customer_id"] = data.get("customer")
            result["subscription_id"] = data.get("subscription")
            result["user_id"] = data.get("metadata", {}).get("user_id")
            result["plan"] = data.get("metadata", {}).get("plan")
            result["processed"] = True

        elif event_type == "customer.subscription.deleted":
            # 订阅取消
            result["subscription_id"] = data.get("id")
            result["customer_id"] = data.get("customer")
            result["processed"] = True

        elif event_type == "invoice.payment_failed":
            # 支付失败
            result["invoice_id"] = data.get("id")
            result["customer_id"] = data.get("customer")
            result["amount"] = data.get("amount_due")
            result["processed"] = True

        return result


# 导出
stripe_client = StripeClient()
payment_service = PaymentService()