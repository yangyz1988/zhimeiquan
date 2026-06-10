import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ platform: string }> }
) {
  const { platform } = await params;
  try {
    const { ok, status, data } = await apiFetch(
      `/api/v1/monitor/rules/${encodeURIComponent(platform)}`
    );
    if (!ok) {
      return NextResponse.json({ error: "规则不存在" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
