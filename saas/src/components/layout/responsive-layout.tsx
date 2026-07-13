"use client";

import React, { useState } from "react";
import { Menu, X, ChevronRight, Home, Settings, HelpCircle, LogOut } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-provider";

interface SidebarItem {
  icon: React.ReactNode;
  label: string;
  href: string;
  badge?: number;
  children?: SidebarItem[];
}

interface ResponsiveLayoutProps {
  children: React.ReactNode;
  sidebarItems: SidebarItem[];
  user?: {
    name: string;
    email: string;
    avatar?: string;
  };
  title?: string;
}

export function ResponsiveLayout({ children, sidebarItems, user, title }: ResponsiveLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  const toggleExpand = (label: string) => {
    setExpandedItems(prev =>
      prev.includes(label) ? prev.filter(i => i !== label) : [...prev, label]
    );
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="p-4 border-b">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
            <span className="text-white font-bold text-sm">智</span>
          </div>
          <span className="font-bold text-lg">{title || "智媒圈"}</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto scrollbar-hide">
        {sidebarItems.map((item, index) => (
          <div key={index}>
            {item.children ? (
              <>
                <button
                  onClick={() => toggleExpand(item.label)}
                  className="flex items-center justify-between w-full px-3 py-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {item.icon}
                    <span className="text-sm">{item.label}</span>
                  </div>
                  <ChevronRight
                    className={`w-4 h-4 transition-transform ${
                      expandedItems.includes(item.label) ? "rotate-90" : ""
                    }`}
                  />
                </button>
                {expandedItems.includes(item.label) && (
                  <div className="ml-4 mt-1 space-y-1">
                    {item.children.map((child, childIndex) => (
                      <Link
                        key={childIndex}
                        href={child.href}
                        className="flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                        onClick={() => setSidebarOpen(false)}
                      >
                        {child.icon}
                        <span className="text-sm">{child.label}</span>
                      </Link>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <Link
                href={item.href}
                className="flex items-center justify-between px-3 py-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                onClick={() => setSidebarOpen(false)}
              >
                <div className="flex items-center gap-3">
                  {item.icon}
                  <span className="text-sm">{item.label}</span>
                </div>
                {item.badge && (
                  <span className="bg-primary text-primary-foreground text-xs px-2 py-0.5 rounded-full">
                    {item.badge}
                  </span>
                )}
              </Link>
            )}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t space-y-2">
        <div className="flex items-center justify-between">
          <ThemeToggle />
          <Button variant="ghost" size="icon">
            <HelpCircle className="w-5 h-5" />
          </Button>
        </div>
        
        {user && (
          <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted cursor-pointer">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              {user.avatar ? (
                <img src={user.avatar} alt={user.name} className="w-8 h-8 rounded-full" />
              ) : (
                <span className="text-white text-xs font-bold">{user.name[0]}</span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user.name}</p>
              <p className="text-xs text-muted-foreground truncate">{user.email}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-card border-r z-50 transform transition-transform lg:hidden ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <SidebarContent />
      </aside>

      {/* Desktop Sidebar */}
      <aside className="fixed top-0 left-0 h-full w-64 bg-card border-r z-30 hidden lg:block">
        <SidebarContent />
      </aside>

      {/* Main Content */}
      <div className="lg:pl-64">
        {/* Top Bar (Mobile) */}
        <header className="sticky top-0 z-20 bg-background/95 backdrop-blur border-b lg:hidden">
          <div className="flex items-center justify-between px-4 h-14">
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(true)}>
              <Menu className="w-5 h-5" />
            </Button>
            <span className="font-bold">{title || "智媒圈"}</span>
            <ThemeToggle />
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}

// 预设侧边栏配置
export const defaultSidebarItems: SidebarItem[] = [
  {
    icon: <Home className="w-5 h-5" />,
    label: "仪表盘",
    href: "/dashboard",
  },
  {
    icon: <Settings className="w-5 h-5" />,
    label: "内容管理",
    href: "#",
    children: [
      { icon: <div className="w-2 h-2 rounded-full bg-blue-500" />, label: "内容列表", href: "/content" },
      { icon: <div className="w-2 h-2 rounded-full bg-green-500" />, label: "媒体资源", href: "/media" },
      { icon: <div className="w-2 h-2 rounded-full bg-purple-500" />, label: "标签体系", href: "/tags" },
    ],
  },
  {
    icon: <Settings className="w-5 h-5" />,
    label: "协作中心",
    href: "#",
    children: [
      { icon: <div className="w-2 h-2 rounded-full bg-orange-500" />, label: "评论管理", href: "/comments" },
      { icon: <div className="w-2 h-2 rounded-full bg-pink-500" />, label: "热点追踪", href: "/trends" },
    ],
  },
  {
    icon: <Settings className="w-5 h-5" />,
    label: "运营中心",
    href: "#",
    children: [
      { icon: <div className="w-2 h-2 rounded-full bg-cyan-500" />, label: "订阅管理", href: "/subscription" },
      { icon: <div className="w-2 h-2 rounded-full bg-yellow-500" />, label: "分发渠道", href: "/channels" },
    ],
  },
];