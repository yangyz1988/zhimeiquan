import { redirect } from "next/navigation";

const clerkKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || "";
const isClerkConfigured = clerkKey.startsWith("pk_") && !clerkKey.includes("your-key");

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  if (isClerkConfigured) {
    const { auth } = await import("@clerk/nextjs/server");
    const { userId } = await auth();
    if (!userId) {
      redirect("/sign-in");
    }
  }
  return <>{children}</>;
}
