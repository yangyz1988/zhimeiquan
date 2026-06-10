"use client";

import { ClerkProvider as RawClerkProvider } from "@clerk/nextjs";

const clerkKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || "";
const isClerkConfigured =
  clerkKey.startsWith("pk_") && !clerkKey.includes("your-key");

export function ClerkProvider({ children }: { children: React.ReactNode }) {
  if (!isClerkConfigured) {
    return <>{children}</>;
  }

  return (
    <RawClerkProvider
      publishableKey={clerkKey}
      appearance={{
        variables: {
          colorPrimary: "#f97316",
        },
      }}
    >
      {children}
    </RawClerkProvider>
  );
}

export { isClerkConfigured };
