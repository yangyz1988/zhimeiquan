import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ platform: string }> }
) {
  const { platform } = await params;
  const { searchParams } = new URL(_request.url);
  const user_id = searchParams.get("user_id") ?? "default";

  try {
    const { ok, status, data } = await apiFetch(
      `/api/v1/fire-score/weights/${encodeURIComponent(platform)}?user_id=${encodeURIComponent(user_id)}`,
      { cache: "no-store" }
    );
    if (!ok) {
      return NextResponse.json({ error: "获取权重失败" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
