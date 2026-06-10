import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET() {
  try {
    const { ok, data } = await apiFetch("/api/v1/ab-test/list", {
      cache: "no-store",
    });
    if (!ok) {
      return NextResponse.json({ tests: [], total: 0 });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ tests: [], total: 0 });
  }
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  try {
    const { ok, status, data } = await apiFetch("/api/v1/ab-test/create", {
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
