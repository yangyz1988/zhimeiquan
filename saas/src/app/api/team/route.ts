import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const user_id = searchParams.get("user_id");

  if (!user_id) {
    return NextResponse.json({ teams: [] });
  }

  try {
    const { ok, status, data } = await apiFetch(
      `/api/v1/team/user/${encodeURIComponent(user_id)}`,
      { cache: "no-store" }
    );
    if (!ok) {
      return NextResponse.json({ teams: [] }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ teams: [] }, { status: 503 });
  }
}

export async function POST(request: NextRequest) {
  const body = await request.json();

  try {
    const { ok, status, data } = await apiFetch("/api/v1/team/create", {
      method: "POST",
      body,
    });
    if (!ok) {
      return NextResponse.json({ error: "创建团队失败" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
