import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET() {
  try {
    const { ok, data } = await apiFetch("/api/v1/analytics/platforms/summary", {
      cache: "no-store",
    });
    if (!ok) {
      return NextResponse.json({ platforms: {} });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ platforms: {} });
  }
}
