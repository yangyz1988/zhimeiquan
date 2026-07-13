import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

// GET /api/trends?platform=...&category=...&min_score=...
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  // 热点详情
  const eventId = searchParams.get("event_id");
  if (eventId) {
    const path = searchParams.get("snapshots")
      ? `/api/v1/trends/${eventId}/snapshots?hours=${searchParams.get("hours") ?? "24"}`
      : `/api/v1/trends/${eventId}`;
    try {
      const { ok, data } = await apiFetch(path, { cache: "no-store" });
      return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
    } catch {
      return NextResponse.json({ event: null }, { status: 503 });
    }
  }

  // 热点列表
  const params = new URLSearchParams();
  for (const [k, v] of searchParams.entries()) {
    if (!["event_id", "snapshots"].includes(k)) params.set(k, v);
  }
  try {
    const { ok, data } = await apiFetch(`/api/v1/trends/?${params}`, { cache: "no-store" });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ events: [], total: 0 }, { status: 503 });
  }
}

// POST /api/trends  (trigger scan)
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    if (body.action === "scan") {
      const { ok, data } = await apiFetch("/api/v1/trends/scan", { method: "POST" });
      return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
    }
    return NextResponse.json({ error: "无效操作" }, { status: 400 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
