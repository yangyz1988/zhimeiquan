"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Zap } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { isClerkConfigured } from "@/components/providers";

function ClerkAuthButton() {
  if (!isClerkConfigured) {
    return (
      <Button size="sm" variant="outline" disabled>
        本地模式
      </Button>
    );
  }

  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { useAuth, UserButton, SignInButton } = require("@clerk/nextjs");
  const { isSignedIn } = useAuth();

  return isSignedIn ? (
    <UserButton
      appearance={{
        elements: { avatarBox: "h-8 w-8" },
      }}
    />
  ) : (
    <SignInButton mode="modal">
      <Button size="sm">登录</Button>
    </SignInButton>
  );
}

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-black/10 backdrop-blur-xl">
      <div className="container flex h-14 items-center">
        <Link href="/" className="flex items-center gap-2">
          <Zap className="h-6 w-6 text-orange-500" />
          <span className="font-bold text-white">智媒圈</span>
        </Link>
        <nav className="ml-auto flex items-center gap-0.5">
          {["/generate", "/monitor", "/tools", "/knowledge", "/experts", "/pricing"].map((path) => {
            const labels: Record<string, string> = {
              "/generate": "生成内容",
              "/monitor": "爆款监控",
              "/tools": "工具箱",
              "/knowledge": "知识体系",
              "/experts": "专家",
              "/pricing": "定价",
            };
            return (
              <Link
                key={path}
                href={path}
                className="px-3 py-2 text-sm text-white/50 hover:text-white transition-colors rounded-md"
              >
                {labels[path]}
              </Link>
            );
          })}
          <ThemeToggle />
          <ClerkAuthButton />
        </nav>
      </div>
    </header>
  );
}
