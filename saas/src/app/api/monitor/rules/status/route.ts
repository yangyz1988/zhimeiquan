import { NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function GET() {
  try {
    const res = await fetch(`${API_URL}/api/v1/monitor/rules/status`, { cache: "no-store" });
    if (!res.ok) {
      return NextResponse.json({ expired: true, age_hours: null });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ expired: true, age_hours: null });
  }
}
