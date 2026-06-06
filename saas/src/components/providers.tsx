"use client";

import { ClerkProvider as RawClerkProvider, useAuth } from "@clerk/nextjs";

export function ClerkProvider({ children }: { children: React.ReactNode }) {
  return (
    <RawClerkProvider
      publishableKey={process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
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
