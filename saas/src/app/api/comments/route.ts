import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

// GET /api/comments?entity_type=...&entity_id=...
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const entity_type = searchParams.get("entity_type");
  const entity_id = searchParams.get("entity_id");
  if (!entity_type || !entity_id) {
    return NextResponse.json({ comments: [], total: 0 });
  }
  try {
    const { ok, data } = await apiFetch(
      `/api/v1/comments/${entity_type}/${entity_id}`,
      { cache: "no-store" }
    );
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ comments: [], total: 0 }, { status: 503 });
  }
}

// POST /api/comments
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { ok, data } = await apiFetch("/api/v1/comments/", { method: "POST", body });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}

// PATCH /api/comments?id=...
export async function PATCH(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");
  if (!id) return NextResponse.json({ error: "缺少评论ID" }, { status: 400 });
  try {
    const body = await request.json();
    const { ok, data } = await apiFetch(`/api/v1/comments/${id}`, { method: "PATCH", body });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}

// DELETE /api/comments?id=...
export async function DELETE(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");
  if (!id) return NextResponse.json({ error: "缺少评论ID" }, { status: 400 });
  try {
    const { ok, data } = await apiFetch(`/api/v1/comments/${id}`, { method: "DELETE" });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
