import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET(_request: NextRequest) {
  try {
    const { ok, data } = await apiFetch("/api/insights/reports");
    if (!ok) {
      return NextResponse.json({ reports: [], total: 0 });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ reports: [], total: 0 });
  }
}
