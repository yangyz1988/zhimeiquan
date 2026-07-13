import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

// GET /api/publish-logs?channel_id=...&status=...
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const params = new URLSearchParams();
  for (const [k, v] of searchParams.entries()) params.set(k, v);

  try {
    const { ok, data } = await apiFetch(`/api/v1/publish-logs/?${params}`, { cache: "no-store" });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ logs: [], total: 0 }, { status: 503 });
  }
}

// POST /api/publish-logs  (retry)
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { log_id, action } = body;
    if (action === "retry" && log_id) {
      const { ok, data } = await apiFetch(`/api/v1/publish-logs/${log_id}/retry`, { method: "POST" });
      return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
    }
    return NextResponse.json({ error: "无效操作" }, { status: 400 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}

// DELETE /api/publish-logs?id=...
export async function DELETE(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");
  if (!id) return NextResponse.json({ error: "缺少日志ID" }, { status: 400 });
  try {
    const { ok, data } = await apiFetch(`/api/v1/publish-logs/${id}`, { method: "DELETE" });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
