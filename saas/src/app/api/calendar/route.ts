import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const year = searchParams.get("year") ?? String(new Date().getFullYear());
  const month = searchParams.get("month") ?? String(new Date().getMonth() + 1);

  try {
    const { ok, status, data } = await apiFetch(
      `/api/v1/calendar/${year}/${month}`,
      { cache: "no-store" }
    );
    if (!ok) {
      return NextResponse.json({ items: [], total: 0 }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ items: [], total: 0 }, { status: 503 });
  }
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const endpoint = body.recurring ? "/api/v1/calendar/recurring" : "/api/v1/calendar/schedule";

  try {
    const { ok, status, data } = await apiFetch(endpoint, {
      method: "POST",
      body,
    });
    if (!ok) {
      return NextResponse.json({ error: "调度失败" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}

export async function PATCH(request: NextRequest) {
  const body = await request.json();
  try {
    const { ok, status, data } = await apiFetch("/api/v1/calendar/schedule", {
      method: "PATCH",
      body,
    });
    if (!ok) {
      return NextResponse.json({ error: "更新失败" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}

export async function DELETE(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const job_id = searchParams.get("job_id");

  if (!job_id) {
    return NextResponse.json({ error: "缺少任务ID" }, { status: 400 });
  }

  try {
    const { ok, status, data } = await apiFetch(
      `/api/v1/calendar/${job_id}`,
      { method: "DELETE" }
    );
    if (!ok) {
      return NextResponse.json({ error: "取消失败" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
