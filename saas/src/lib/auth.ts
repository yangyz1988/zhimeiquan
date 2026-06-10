import { type NextRequest, NextResponse } from "next/server";

const clerkKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || "";
const isClerkConfigured =
  clerkKey.startsWith("pk_") && !clerkKey.includes("your-key");

export async function requireAuth(
  request?: NextRequest,
): Promise<{ userId: string } | NextResponse> {
  if (!isClerkConfigured) {
    return { userId: "local-user" };
  }
  const { auth } = await import("@clerk/nextjs/server");
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "未登录" }, { status: 401 });
  }
  return { userId };
}
