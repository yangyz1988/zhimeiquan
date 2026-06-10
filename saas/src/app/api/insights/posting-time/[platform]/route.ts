import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ platform: string }> },
) {
  const { platform } = await params;
  try {
    const { ok, data } = await apiFetch(
      `/api/v1/insights/posting-time/${encodeURIComponent(platform)}`,
    );
    if (!ok) return NextResponse.json({ time_slots: [] });
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ time_slots: [] });
  }
}
