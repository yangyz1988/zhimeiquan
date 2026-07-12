import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const category = searchParams.get("category");
  const platform = searchParams.get("platform");

  let path = "/api/v1/templates/list";
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (platform) params.set("platform", platform);
  if (params.toString()) path += `?${params.toString()}`;

  try {
    const { ok, data } = await apiFetch(path, { cache: "no-store" });
    if (!ok) {
      return NextResponse.json({ templates: [], total: 0 });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ templates: [], total: 0 }, { status: 503 });
  }
}

export async function POST(request: NextRequest) {
  const body = await request.json();

  try {
    const { ok, status, data } = await apiFetch("/api/v1/templates/", {
      method: "POST",
      body,
    });
    if (!ok) {
      return NextResponse.json({ error: "创建失败" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
