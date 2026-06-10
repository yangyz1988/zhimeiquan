import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ platform: string }> },
) {
  const { platform } = await params;
  try {
    const { ok, data } = await apiFetch(
      `/api/v1/insights/trends/${encodeURIComponent(platform)}?days=7`,
    );
    if (!ok) return NextResponse.json({ trends: [], hot_topics: [] });
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ trends: [], hot_topics: [] });
  }
}
