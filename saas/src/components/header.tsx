"use client";

import Link from "next/link";
import { useAuth, UserButton, SignInButton } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import { Zap } from "lucide-react";

export function Header() {
  const { isSignedIn } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <Link href="/" className="flex items-center space-x-2">
          <Zap className="h-6 w-6 text-orange-500" />
          <span className="font-bold">智媒圈</span>
        </Link>
        <nav className="ml-auto flex items-center space-x-4">
          <Link href="/dashboard" className="text-sm text-muted-foreground hover:text-foreground">
            工作台
          </Link>
          <Link href="/generate" className="text-sm text-muted-foreground hover:text-foreground">
            生成内容
          </Link>
          <Link href="/monitor" className="text-sm text-muted-foreground hover:text-foreground">
            爆款监控
          </Link>
          <Link href="/analytics" className="text-sm text-muted-foreground hover:text-foreground">
            数据分析
          </Link>
          <Link href="/calendar" className="text-sm text-muted-foreground hover:text-foreground">
            内容日历
          </Link>
          {isSignedIn ? (
            <UserButton
              appearance={{
                elements: {
                  avatarBox: "h-8 w-8",
                },
              }}
            />
          ) : (
            <SignInButton mode="modal">
              <Button size="sm">登录</Button>
            </SignInButton>
          )}
        </nav>
      </div>
    </header>
  );
}
