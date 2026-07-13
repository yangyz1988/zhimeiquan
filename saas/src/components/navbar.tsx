"use client";

import { useState } from "react";
import { Bell, ChevronDown, LogOut, Moon, Settings, User, Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-provider";

const navigation = [
  { name: "仪表盘", href: "/dashboard" },
  { name: "内容", href: "/content" },
  { name: "媒体", href: "/media" },
  { name: "评论", href: "/comments" },
  { name: "标签", href: "/tags" },
  { name: "订阅", href: "/subscription" },
  { name: "渠道", href: "/channels" },
  { name: "热点", href: "/trends" },
];

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  const isActive = (href: string) => {
    return pathname?.startsWith(href) ?? false;
  };

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        {/* Logo */}
        <Link href="/" className="mr-6 flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
            <span className="text-white font-bold text-sm">智</span>
          </div>
          <span className="font-bold text-lg hidden sm:inline-block">智媒圈</span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center space-x-1 flex-1">
          {navigation.slice(0, 5).map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive(item.href)
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              }`}
            >
              {item.name}
            </Link>
          ))}
          
          {/* 更多菜单 */}
          <div className="relative group">
            <button className="px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted flex items-center gap-1">
              更多 <ChevronDown className="w-4 h-4" />
            </button>
            <div className="absolute top-full left-0 mt-1 w-40 bg-card border rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
              {navigation.slice(5).map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="block px-4 py-2 text-sm hover:bg-muted first:rounded-t-lg last:rounded-b-lg"
                >
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2 ml-auto">
          {/* 搜索按钮 */}
          <Button variant="ghost" size="icon" className="hidden sm:flex">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </Button>

          {/* 主题切换 */}
          <ThemeToggle />

          {/* 通知 */}
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="w-5 h-5" />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full" />
          </Button>

          {/* 用户菜单 */}
          <div className="relative group">
            <Button variant="ghost" className="gap-2 pl-2 pr-3">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                <span className="text-white text-xs font-bold">杨</span>
              </div>
              <span className="hidden sm:inline text-sm">杨老板</span>
              <ChevronDown className="w-4 h-4" />
            </Button>
            
            {/* 下拉菜单 */}
            <div className="absolute top-full right-0 mt-1 w-56 bg-card border rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
              <div className="p-3 border-b">
                <p className="font-medium">杨老板</p>
                <p className="text-sm text-muted-foreground">boss@zhimeiquan.com</p>
              </div>
              <div className="p-1">
                <Link href="/settings" className="flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-muted">
                  <Settings className="w-4 h-4" /> 设置
                </Link>
                <Link href="/profile" className="flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-muted">
                  <User className="w-4 h-4" /> 个人资料
                </Link>
                <hr className="my-1" />
                <button className="flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-muted text-red-500 w-full">
                  <LogOut className="w-4 h-4" /> 退出登录
                </button>
              </div>
            </div>
          </div>

          {/* 移动端菜单按钮 */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </Button>
        </div>
      </div>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t">
          <div className="container py-4 space-y-1">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-3 py-2 rounded-md text-sm font-medium ${
                  isActive(item.href)
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                {item.name}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}