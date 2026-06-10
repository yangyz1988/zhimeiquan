import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ projectId: string }> },
) {
  const { projectId } = await params;
  try {
    const { ok, data } = await apiFetch(`/api/v1/analytics/${projectId}`, {
      cache: "no-store",
    });
    if (!ok) {
      return NextResponse.json({
        total_content: 0,
        total_views: 0,
        total_likes: 0,
        total_comments: 0,
        total_shares: 0,
        avg_engagement: 0,
        content_list: [],
      });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({
      total_content: 0,
      total_views: 0,
      total_likes: 0,
      total_comments: 0,
      total_shares: 0,
      avg_engagement: 0,
      content_list: [],
    });
  }
}
