import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const user_id = searchParams.get("user_id");

  if (!user_id) {
    return NextResponse.json({ competitors: [] });
  }

  try {
    const { ok, data } = await apiFetch(
      `/api/v1/competitors/list?user_id=${encodeURIComponent(user_id)}`,
      { cache: "no-store" }
    );
    if (!ok) {
      return NextResponse.json({ competitors: [] });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ competitors: [] });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { ok, status, data } = await apiFetch("/api/v1/competitors/add", {
      method: "POST",
      body,
    });
    if (!ok) {
      return NextResponse.json(data, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
