import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

// GET /api/channels?platform=...
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");
  const endpoint = id ? `/api/v1/channels/${id}` : "/api/v1/channels/";
  const params = new URLSearchParams();
  for (const [k, v] of searchParams.entries()) {
    if (k !== "id") params.set(k, v);
  }

  try {
    const { ok, data } = await apiFetch(`${endpoint}?${params}`, { cache: "no-store" });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ channels: [] }, { status: 503 });
  }
}

// POST /api/channels
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { ok, data } = await apiFetch("/api/v1/channels/", { method: "POST", body });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}

// PATCH /api/channels?id=...
export async function PATCH(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");
  if (!id) return NextResponse.json({ error: "缺少渠道ID" }, { status: 400 });
  try {
    const body = await request.json();
    const { ok, data } = await apiFetch(`/api/v1/channels/${id}`, { method: "PATCH", body });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}

// DELETE /api/channels?id=...
export async function DELETE(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");
  if (!id) return NextResponse.json({ error: "缺少渠道ID" }, { status: 400 });
  try {
    const { ok, data } = await apiFetch(`/api/v1/channels/${id}`, { method: "DELETE" });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
