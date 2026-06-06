import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function GET() {
  try {
    const res = await fetch(`${API_URL}/api/v1/monitor/rules`, { cache: "no-store" });
    if (!res.ok) {
      return NextResponse.json({ updated_at: null, platforms: [], rules: {} });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ updated_at: null, platforms: [], rules: {} });
  }
}
