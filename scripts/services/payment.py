"""Stripe 支付服务"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

import stripe

from services.logging import logger

PLAN_PRICES = {
    "free": {
        "amount": 0,
        "name": "免费版",
        "description": "每日 5 次生成 · 3 个平台",
    },
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

# 前端 tier 名到后端 plan key 的映射
TIER_TO_PLAN: dict[str, str] = {
    "免费版": "free",
    "进阶版": "basic",
    "高级版": "pro",
    "旗舰版": "enterprise",
}


class PaymentService:
    """Stripe 支付集成"""

    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    def create_checkout_session(
        self, user_id: str, plan: str, success_url: str, cancel_url: str
    ) -> dict:
        """创建 Stripe Checkout 会话"""
        price_info = PLAN_PRICES.get(plan)
        if not price_info:
            return {"error": "无效的套餐"}

        if plan == "free":
            return {"error": "免费版无需创建支付会话"}

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card", "alipay", "wechat_pay"],
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
                allow_promotion_codes=True,
                billing_address_collection="auto",
            )
            logger.info(
                "Stripe Checkout 会话已创建",
                user_id=user_id,
                plan=plan,
                session_id=session.id,
            )
            return {"session_id": session.id, "url": session.url}
        except stripe.error.StripeError as e:
            logger.error("Stripe 创建会话失败", error=str(e), user_id=user_id, plan=plan)
            return {"error": f"支付服务异常: {e.user_message or str(e)}"}
        except Exception as e:
            logger.error("创建支付会话时发生未知错误", error=str(e))
            return {"error": "内部服务错误，请稍后重试"}

    def verify_webhook(self, payload: bytes, sig_header: str) -> Optional[stripe.Event]:
        """
        验证 Stripe Webhook 签名

        使用 stripe.Webhook.construct_event() 验证签名，
        防止恶意伪造的 webhook 请求。

        Args:
            payload: 原始请求体（bytes）
            sig_header: Stripe-Signature 请求头

        Returns:
            验证通过后返回 Stripe Event 对象；验证失败返回 None

        Raises:
            ValueError: webhook secret 未配置时抛出
        """
        if not self.webhook_secret:
            logger.error("Webhook 验证失败：STRIPE_WEBHOOK_SECRET 未配置")
            raise ValueError("STRIPE_WEBHOOK_SECRET 未配置，无法验证 Webhook 签名")

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=self.webhook_secret,
            )
            logger.info(
                "Webhook 签名验证通过",
                event_type=event.type,
                event_id=event.id,
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(
                "Webhook 签名验证失败",
                error=str(e),
                sig_header_preview=sig_header[:50] if sig_header else "missing",
            )
            return None
        except ValueError as e:
            logger.error("Webhook payload 解析失败", error=str(e))
            return None

    def _get_db(self) -> sqlite3.Connection:
        """获取数据库连接（自管理，不依赖外部 database 模块）"""
        db_url = os.getenv("DATABASE_URL", "file:./dev.db")
        db_path = db_url.replace("sqlite:", "").replace("file:", "").lstrip("/")
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")

        # 确保订阅表存在
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                user_id TEXT PRIMARY KEY,
                plan TEXT NOT NULL DEFAULT 'free',
                stripe_subscription_id TEXT,
                status TEXT NOT NULL DEFAULT 'inactive',
                current_period_end INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        return conn

    def handle_subscription_updated(self, event: stripe.Event) -> dict:
        """
        处理 customer.subscription.updated 事件

        从订阅 metadata 中提取 user_id 和 plan，
        更新数据库中用户的订阅状态。

        Args:
            event: 已验证的 Stripe Event 对象

        Returns:
            处理结果字典
        """
        subscription = event.data.object  # type: ignore[attr-defined]
        if not isinstance(subscription, stripe.Subscription):
            return {"error": "事件数据不是订阅对象"}

        user_id = subscription.metadata.get("user_id", "")
        plan = subscription.metadata.get("plan", "")
        status = subscription.status
        current_period_end = subscription.current_period_end

        if not user_id:
            logger.warning("订阅事件缺少 user_id metadata", subscription_id=subscription.id)
            return {"error": "订阅缺少 user_id metadata"}

        try:
            conn = self._get_db()
            conn.execute(
                """INSERT INTO user_subscriptions (user_id, plan, stripe_subscription_id, status, current_period_end, updated_at)
                   VALUES (?, ?, ?, ?, ?, datetime('now'))
                   ON CONFLICT(user_id) DO UPDATE SET
                       plan = excluded.plan,
                       stripe_subscription_id = excluded.stripe_subscription_id,
                       status = excluded.status,
                       current_period_end = excluded.current_period_end,
                       updated_at = excluded.updated_at""",
                (user_id, plan, subscription.id, status, current_period_end),
            )
            conn.commit()
            conn.close()

            logger.info(
                "用户订阅已更新",
                user_id=user_id,
                plan=plan,
                status=status,
                subscription_id=subscription.id,
            )
            return {
                "success": True,
                "user_id": user_id,
                "plan": plan,
                "status": status,
            }
        except Exception as e:
            logger.error("更新用户订阅失败", error=str(e), user_id=user_id)
            return {"error": f"数据库更新失败: {str(e)}"}

    def handle_subscription_updated_from_checkout(
        self, user_id: str, plan: str, subscription_id: str
    ) -> dict:
        """
        从 checkout 完成事件更新用户订阅

        Args:
            user_id: 用户ID
            plan: 套餐标识
            subscription_id: Stripe订阅ID

        Returns:
            处理结果字典
        """
        try:
            # 获取订阅详情
            subscription = stripe.Subscription.retrieve(subscription_id)
            status = subscription.status
            current_period_end = subscription.current_period_end

            conn = self._get_db()
            conn.execute(
                """INSERT INTO user_subscriptions (user_id, plan, stripe_subscription_id, status, current_period_end, updated_at)
                   VALUES (?, ?, ?, ?, ?, datetime('now'))
                   ON CONFLICT(user_id) DO UPDATE SET
                       plan = excluded.plan,
                       stripe_subscription_id = excluded.stripe_subscription_id,
                       status = excluded.status,
                       current_period_end = excluded.current_period_end,
                       updated_at = excluded.updated_at""",
                (user_id, plan, subscription_id, status, current_period_end),
            )
            conn.commit()
            conn.close()

            logger.info(
                "从Checkout更新用户订阅成功",
                user_id=user_id,
                plan=plan,
                status=status,
                subscription_id=subscription_id,
            )
            return {
                "success": True,
                "user_id": user_id,
                "plan": plan,
                "status": status,
            }
        except Exception as e:
            logger.error("从Checkout更新用户订阅失败", error=str(e), user_id=user_id)
            return {"error": f"数据库更新失败: {str(e)}"}

    def cancel_user_subscription(self, user_id: str) -> dict:
        """
        取消用户订阅（标记为已取消）

        Args:
            user_id: 用户ID

        Returns:
            处理结果字典
        """
        try:
            conn = self._get_db()
            conn.execute(
                """UPDATE user_subscriptions 
                   SET status = 'canceled', updated_at = datetime('now')
                   WHERE user_id = ?""",
                (user_id,),
            )
            conn.commit()
            conn.close()

            logger.info("用户订阅已取消", user_id=user_id)
            return {"success": True, "user_id": user_id, "status": "canceled"}
        except Exception as e:
            logger.error("取消用户订阅失败", error=str(e), user_id=user_id)
            return {"error": f"数据库更新失败: {str(e)}"}

    def create_usage_record(self, subscription_item_id: str, quantity: int) -> dict:
        """记录使用量（按量计费）"""
        try:
            record = stripe.UsageRecord.create(
                subscription_item=subscription_item_id,
                quantity=quantity,
                timestamp=int(__import__("time").time()),
            )
            return {"record_id": record.id}
        except stripe.error.StripeError as e:
            logger.error("Stripe 用量记录失败", error=str(e))
            return {"error": f"用量记录失败: {e.user_message or str(e)}"}
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
        except stripe.error.StripeError as e:
            logger.error("获取订阅信息失败", error=str(e), subscription_id=subscription_id)
            return {"error": f"获取订阅失败: {e.user_message or str(e)}"}
        except Exception as e:
            return {"error": str(e)}

    def cancel_subscription(self, subscription_id: str) -> dict:
        """取消订阅"""
        try:
            sub = stripe.Subscription.delete(subscription_id)
            return {"id": sub.id, "status": "canceled"}
        except stripe.error.StripeError as e:
            logger.error("取消订阅失败", error=str(e), subscription_id=subscription_id)
            return {"error": f"取消失败: {e.user_message or str(e)}"}
        except Exception as e:
            return {"error": str(e)}

    def get_user_subscription(self, user_id: str) -> dict:
        """获取用户当前订阅状态"""
        try:
            conn = self._get_db()
            cursor = conn.execute(
                "SELECT * FROM user_subscriptions WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "user_id": row["user_id"],
                    "plan": row["plan"],
                    "status": row["status"],
                    "stripe_subscription_id": row["stripe_subscription_id"],
                    "current_period_end": row["current_period_end"],
                }
            return {"plan": "free", "status": "inactive"}
        except Exception as e:
            logger.error("获取用户订阅失败", error=str(e), user_id=user_id)
            return {"error": str(e)}
