import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

/**
 * Stripe Webhook 接收端点
 *
 * Stripe 会向此端点发送 webhook 事件。
 * 我们将原始请求转发到 Python 后端进行签名验证和处理。
 *
 * 注意：Stripe webhook 请求体需要以原始 bytes 形式传递，
 * 因此不能使用 apiFetch 的 JSON 序列化，需要直接使用 fetch。
 */
export async function POST(request: NextRequest) {
  const body = await request.text();
  const sigHeader = request.headers.get("stripe-signature");

  if (!sigHeader) {
    return NextResponse.json(
      { error: "缺少 stripe-signature 请求头" },
      { status: 400 }
    );
  }

  const API_URL = process.env.API_URL || "http://localhost:8000";

  try {
    const res = await fetch(`${API_URL}/api/v1/payment/webhook`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "stripe-signature": sigHeader,
      },
      body,
    });

    // 不修改响应，直接透传
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json(
      { error: "Webhook 处理服务不可用" },
      { status: 503 }
    );
  }
}
