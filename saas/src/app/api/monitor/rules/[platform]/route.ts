import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ platform: string }> }
) {
  const { platform } = await params;
  try {
    const res = await fetch(`${API_URL}/api/v1/monitor/rules/${encodeURIComponent(platform)}`);
    if (!res.ok) {
      return NextResponse.json({ error: "规则不存在" }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
