"""Stripe 支付服务"""

import os
import stripe


class PaymentService:
    """Stripe 支付集成"""

    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    def create_checkout_session(
        self, user_id: str, plan: str, success_url: str, cancel_url: str
    ) -> dict:
        """创建 Stripe Checkout 会话"""
        prices = {
            "basic": {
                "amount": 4900,
                "name": "基础版",
                "description": "每月 100 次生成",
            },
            "pro": {
                "amount": 9900,
                "name": "专业版",
                "description": "每月 500 次生成 + 视频",
            },
            "enterprise": {
                "amount": 19900,
                "name": "企业版",
                "description": "无限生成 + 优先支持",
            },
        }

        price_info = prices.get(plan)
        if not price_info:
            return {"error": "无效的套餐"}

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "cny",
                            "product_data": {
                                "name": f"智媒圈 {price_info['name']}",
                                "description": price_info["description"],
                            },
                            "unit_amount": price_info["amount"],
                            "recurring": {"interval": "month"},
                        },
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"user_id": user_id, "plan": plan},
            )
            return {"session_id": session.id, "url": session.url}
        except Exception as e:
            return {"error": str(e)}

    def create_usage_record(self, subscription_item_id: str, quantity: int) -> dict:
        """记录使用量（按量计费）"""
        try:
            record = stripe.UsageRecord.create(
                subscription_item=subscription_item_id,
                quantity=quantity,
                timestamp=int(__import__("time").time()),
            )
            return {"record_id": record.id}
        except Exception as e:
            return {"error": str(e)}

    def get_subscription(self, subscription_id: str) -> dict:
        """获取订阅信息"""
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": sub.id,
                "status": sub.status,
                "plan": sub.metadata.get("plan"),
                "current_period_end": sub.current_period_end,
            }
        except Exception as e:
            return {"error": str(e)}

    def cancel_subscription(self, subscription_id: str) -> dict:
        """取消订阅"""
        try:
            sub = stripe.Subscription.delete(subscription_id)
            return {"id": sub.id, "status": "canceled"}
        except Exception as e:
            return {"error": str(e)}
