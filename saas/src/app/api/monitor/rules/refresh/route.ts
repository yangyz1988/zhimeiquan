import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function POST() {
  try {
    const { ok, status, data } = await apiFetch("/api/v1/monitor/rules/refresh", {
      method: "POST",
    });
    if (!ok) {
      return NextResponse.json({ error: "刷新失败" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
