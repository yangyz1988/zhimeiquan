import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const { searchParams } = new URL(request.url);
  const action = searchParams.get("action") || "analyze";

  try {
    if (action === "compare") {
      const user_id = searchParams.get("user_id");
      if (!user_id) {
        return NextResponse.json({ error: "缺少 user_id 参数" }, { status: 400 });
      }
      const { ok, data } = await apiFetch(
        `/api/v1/competitors/compare/${encodeURIComponent(id)}?user_id=${encodeURIComponent(user_id)}`
      );
      if (!ok) return NextResponse.json({ error: "对比数据不存在" }, { status: 404 });
      return NextResponse.json(data);
    }

    const { ok, data } = await apiFetch(
      `/api/v1/competitors/analyze/${encodeURIComponent(id)}`
    );
    if (!ok) return NextResponse.json({ error: "分析数据不存在" }, { status: 404 });
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const { ok, status, data } = await apiFetch(
      `/api/v1/competitors/${encodeURIComponent(id)}`,
      { method: "DELETE" }
    );
    if (!ok) return NextResponse.json(data, { status });
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
