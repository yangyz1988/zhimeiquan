import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(_request: NextRequest) {
  try {
    const { ok, status, data } = await apiFetch("/api/v1/agent/tasks", {
      cache: "no-store",
    });
    if (!ok) {
      return NextResponse.json({ tasks: [], total: 0 }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ tasks: [], total: 0 }, { status: 503 });
  }
}

export async function POST(request: NextRequest) {
  const body = await request.json();

  try {
    const { ok, status, data } = await apiFetch("/api/v1/agent/create", {
      method: "POST",
      body,
    });
    if (!ok) {
      return NextResponse.json({ error: "创建任务失败" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
