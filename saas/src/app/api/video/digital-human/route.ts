import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function POST(request: NextRequest) {
  const { userId } = await import("@clerk/nextjs/server").then((m) =>
    m.auth(),
  );
  if (!userId) {
    return NextResponse.json({ error: "未登录" }, { status: 401 });
  }
  const body = await request.json();
  try {
    const { ok, status, data } = await apiFetch(
      "/api/v1/video/digital-human",
      {
        method: "POST",
        body,
      },
    );
    if (!ok) {
      return NextResponse.json({ error: "生成失败" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
