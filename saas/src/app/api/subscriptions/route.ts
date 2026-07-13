import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

// GET /api/subscriptions  →  /api/v1/subscriptions/
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const subpath = searchParams.get("invoices") ? "/invoices" : "/";

  if (subpath === "/invoices") {
    const page = searchParams.get("page") ?? "1";
    try {
      const { ok, data } = await apiFetch(`/api/v1/subscriptions/invoices?page=${page}`, { cache: "no-store" });
      return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
    } catch {
      return NextResponse.json({ invoices: [], total: 0 }, { status: 503 });
    }
  }

  try {
    const { ok, data } = await apiFetch("/api/v1/subscriptions/", { cache: "no-store" });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}

// POST /api/subscriptions  (通用: upgrade/cancel/resume)
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const endpoint = body.action === "cancel" ? "/api/v1/subscriptions/cancel"
      : body.action === "resume" ? "/api/v1/subscriptions/resume"
      : "/api/v1/subscriptions/upgrade";
    const { ok, data } = await apiFetch(endpoint, { method: "POST", body });
    return ok ? NextResponse.json(data) : NextResponse.json(data, { status: 502 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
