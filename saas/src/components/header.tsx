"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Zap, Menu, X } from "lucide-react";
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

const NAV_LINKS = [
  { path: "/generate", label: "生成内容" },
  { path: "/monitor", label: "爆款监控" },
  { path: "/tools", label: "工具箱" },
  { path: "/knowledge", label: "知识体系" },
  { path: "/experts", label: "专家" },
  { path: "/pricing", label: "定价" },
  { path: "/settings", label: "设置" },
] as const;

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-black/10 backdrop-blur-xl">
      <div className="container flex h-14 items-center px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <Zap className="h-5 w-5 sm:h-6 sm:w-6 text-orange-500" />
          <span className="font-bold text-white text-sm sm:text-base">智媒圈</span>
        </Link>

        {/* Desktop nav — hidden on mobile, visible from md */}
        <nav className="ml-auto hidden md:flex items-center gap-0.5">
          {NAV_LINKS.map(({ path, label }) => (
            <Link
              key={path}
              href={path}
              className="px-3 py-2 text-sm text-white/50 hover:text-white transition-colors rounded-md"
            >
              {label}
            </Link>
          ))}
          <div className="ml-2 flex items-center gap-1">
            <ThemeToggle />
            <ClerkAuthButton />
          </div>
        </nav>

        {/* Mobile hamburger + quick actions — visible below md */}
        <div className="ml-auto flex md:hidden items-center gap-1">
          <ThemeToggle />
          <ClerkAuthButton />
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileMenuOpen(true)}
            className="text-white/60 hover:text-white hover:bg-white/10"
            aria-label="打开菜单"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Mobile slide-out menu */}
      {mobileMenuOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />

          {/* Drawer */}
          <div className="fixed top-0 right-0 z-50 h-full w-64 bg-black/95 backdrop-blur-xl border-l border-white/10 md:hidden animate-in slide-in-from-right">
            <div className="flex items-center justify-between p-4 border-b border-white/10">
              <span className="font-bold text-white text-sm">导航</span>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setMobileMenuOpen(false)}
                className="text-white/60 hover:text-white hover:bg-white/10"
                aria-label="关闭菜单"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
            <nav className="flex flex-col p-4 gap-1">
              {NAV_LINKS.map(({ path, label }) => (
                <Link
                  key={path}
                  href={path}
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 text-sm text-white/60 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                >
                  {label}
                </Link>
              ))}
            </nav>
          </div>
        </>
      )}
    </header>
  );
}
