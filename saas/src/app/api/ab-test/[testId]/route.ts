import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ testId: string }> },
) {
  const { testId } = await params;
  try {
    const { ok, data } = await apiFetch(`/api/v1/ab-test/${testId}/result`);
    if (!ok) {
      return NextResponse.json({ error: "未找到" }, { status: 404 });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
