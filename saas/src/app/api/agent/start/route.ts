import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function POST(request: NextRequest) {
  const body = await request.json();

  try {
    const { ok, status, data } = await apiFetch("/api/v1/agent/start", {
      method: "POST",
      body,
    });
    if (!ok) {
      return NextResponse.json({ error: "启动 Agent 失败" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
