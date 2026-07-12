import { NextRequest } from "next/server";
import { requireAuth } from "@/lib/auth";

const API_URL = process.env.API_URL || "http://localhost:8000";
const API_SECRET = process.env.API_SECRET || "";

export async function POST(request: NextRequest) {
  const authResult = await requireAuth();
  if ("status" in authResult) return authResult;

  const body = await request.json();

  try {
    const backendUrl = `${API_URL}/api/v1/stream/generate`;

    const response = await fetch(backendUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(API_SECRET ? { "X-API-Key": API_SECRET } : {}),
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      return new Response(
        JSON.stringify({ error: "流式生成失败" }),
        { status: response.status, headers: { "Content-Type": "application/json" } }
      );
    }

    // SSE 数据不做解析，直接透传
    return new Response(response.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
      },
    });
  } catch {
    return new Response(
      JSON.stringify({ error: "API 服务未启动" }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }
}
