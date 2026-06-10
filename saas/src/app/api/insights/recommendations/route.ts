import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function POST(request: NextRequest) {
  const body = await request.json();
  try {
    const { ok, data } = await apiFetch("/api/v1/insights/recommendations", {
      method: "POST",
      body,
    });
    if (!ok) return NextResponse.json({ hook_type: "数字型", title_templates: [] });
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ hook_type: "数字型", title_templates: [] });
  }
}
