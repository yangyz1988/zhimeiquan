import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

export async function POST(request: NextRequest) {
  const authResult = await requireAuth();
  if ("status" in authResult) return authResult;
  const { userId } = authResult;

  let body: { plan?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "请求体格式无效" }, { status: 400 });
  }

  const { plan } = body;
  if (!plan || typeof plan !== "string") {
    return NextResponse.json({ error: "请指定套餐类型 (plan)" }, { status: 400 });
  }

  const allowedPlans = ["basic", "pro", "enterprise"];
  if (!allowedPlans.includes(plan)) {
    return NextResponse.json({ error: "无效的套餐类型" }, { status: 400 });
  }

  const appUrl = process.env.NEXT_PUBLIC_APP_URL || request.nextUrl.origin;
  const successUrl = `${appUrl}/dashboard?checkout=success`;
  const cancelUrl = `${appUrl}/pricing?checkout=canceled`;

  try {
    const result = await apiFetch("/api/v1/payment/subscribe", {
      method: "POST",
      body: {
        user_id: userId,
        plan,
        success_url: successUrl,
        cancel_url: cancelUrl,
      },
    });

    if (!result.ok) {
      return NextResponse.json(
        { error: result.error || "创建支付会话失败" },
        { status: result.status }
      );
    }

    return NextResponse.json(result.data);
  } catch {
    return NextResponse.json({ error: "支付服务暂不可用" }, { status: 503 });
  }
}
