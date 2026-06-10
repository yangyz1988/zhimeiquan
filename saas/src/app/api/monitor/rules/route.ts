import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET() {
  try {
    const { ok, data } = await apiFetch("/api/v1/monitor/rules", {
      cache: "no-store",
    });
    if (!ok) {
      return NextResponse.json({ updated_at: null, platforms: [], rules: {} });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ updated_at: null, platforms: [], rules: {} });
  }
}
