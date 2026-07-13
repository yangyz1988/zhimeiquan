import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

// GET /api/tags?group_id=...&q=...
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const path = searchParams.get("groups") ? "/api/v1/tags/groups" : "/api/v1/tags/";
  const params = new URLSearchParams();
  for (const [k, v] of searchParams.entries()) {
    if (k !== "groups") params.set(k, v);
  }
  try {
    const { ok, data } = await apiFetch(`${path}?${params}`, { cache: "no-store" });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ tags: [], total: 0 }, { status: 503 });
  }
}

// POST /api/tags  (body: { name, slug?, color? })
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const path = body.group_name ? "/api/v1/tags/groups" : "/api/v1/tags/";
    const { ok, data } = await apiFetch(path, { method: "POST", body });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}

// DELETE /api/tags?id=...
export async function DELETE(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");
  if (!id) return NextResponse.json({ error: "缺少ID" }, { status: 400 });
  try {
    const { ok, data } = await apiFetch(`/api/v1/tags/${id}`, { method: "DELETE" });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
