import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function POST() {
  try {
    const res = await fetch(`${API_URL}/api/v1/monitor/rules/refresh`, {
      method: "POST",
    });
    if (!res.ok) {
      return NextResponse.json({ error: "刷新失败" }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
