import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export async function GET() {
  try {
    const { ok, data } = await apiFetch("/api/v1/monitor/rules/status", {
      cache: "no-store",
    });
    if (!ok) {
      return NextResponse.json({ expired: true, age_hours: null });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ expired: true, age_hours: null });
  }
}
