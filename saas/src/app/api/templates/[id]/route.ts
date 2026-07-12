import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const { ok, status, data } = await apiFetch(`/api/v1/templates/${id}`, {
      cache: "no-store",
    });
    if (!ok) {
      return NextResponse.json({ error: "模板不存在" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();

  try {
    const { ok, status, data } = await apiFetch(`/api/v1/templates/${id}`, {
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

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const { ok, status, data } = await apiFetch(`/api/v1/templates/${id}`, {
      method: "DELETE",
    });
    if (!ok) {
      return NextResponse.json({ error: "删除失败" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
