import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

// GET /api/media  →  /api/v1/media/list
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const folder = searchParams.get("folder");
  const mime_type = searchParams.get("mime_type");
  const page = searchParams.get("page") ?? "1";
  const limit = searchParams.get("limit") ?? "20";

  const params = new URLSearchParams({ page, limit });
  if (folder) params.set("folder", folder);
  if (mime_type) params.set("mime_type", mime_type);

  try {
    const { ok, data } = await apiFetch(`/api/v1/media/list?${params}`, { cache: "no-store" });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ assets: [], total: 0 }, { status: 503 });
  }
}

// POST /api/media  →  /api/v1/media/upload
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { ok, data } = await apiFetch("/api/v1/media/upload", { method: "POST", body });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}

// DELETE /api/media?asset_id=...  →  /api/v1/media/{id}
export async function DELETE(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("asset_id");
  if (!id) return NextResponse.json({ error: "缺少资产ID" }, { status: 400 });
  try {
    const { ok, data } = await apiFetch(`/api/v1/media/${id}`, { method: "DELETE" });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
