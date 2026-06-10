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
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <Link href="/" className="flex items-center space-x-2">
          <Zap className="h-6 w-6 text-orange-500" />
          <span className="font-bold">智媒圈</span>
        </Link>
        <nav className="ml-auto flex items-center space-x-1">
          <Link href="/generate" className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground rounded-md hover:bg-accent">
            生成内容
          </Link>
          <Link href="/monitor" className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground rounded-md hover:bg-accent">
            爆款监控
          </Link>
          <Link href="/tools" className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground rounded-md hover:bg-accent">
            工具箱
          </Link>
          <Link href="/knowledge" className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground rounded-md hover:bg-accent">
            知识体系
          </Link>
          <Link href="/experts" className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground rounded-md hover:bg-accent">
            专家
          </Link>
          <Link href="/pricing" className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground rounded-md hover:bg-accent">
            定价
          </Link>
          <ThemeToggle />
          <ClerkAuthButton />
        </nav>
      </div>
    </header>
  );
}
