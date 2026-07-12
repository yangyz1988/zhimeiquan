import { type NextRequest, NextResponse } from "next/server";

const clerkKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || "";
const isClerkConfigured =
  clerkKey.startsWith("pk_") && !clerkKey.includes("your-key");

export type AuthResult = { userId: string };

/** 类型守卫：检查 requireAuth 的返回值是否为 {userId: string} */
export function isAuthResult(obj: unknown): obj is AuthResult {
  return (
    typeof obj === "object" &&
    obj !== null &&
    "userId" in obj &&
    typeof (obj as Record<string, unknown>).userId === "string"
  );
}

export async function requireAuth(
  request?: NextRequest,
): Promise<AuthResult | NextResponse> {
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
