import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const action = body.action;
  delete body.action;

  try {
    if (action === "report") {
      const { ok, status, data } = await apiFetch("/api/v1/fire-score/report", {
        method: "POST",
        body,
      });
      if (!ok) {
        return NextResponse.json({ error: "上报失败" }, { status });
      }
      return NextResponse.json(data);
    }

    if (action === "calibrate") {
      const { ok, status, data } = await apiFetch("/api/v1/fire-score/calibrate", {
        method: "POST",
        body,
      });
      if (!ok) {
        return NextResponse.json({ error: "校准失败" }, { status });
      }
      return NextResponse.json(data);
    }

    return NextResponse.json({ error: "未知操作" }, { status: 400 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
