"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Home,
  Sparkles,
  TrendingUp,
  Library,
  PanelRightOpen,
  type LucideIcon,
} from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "首页", icon: Home },
  { href: "/generate", label: "生成", icon: Sparkles },
  { href: "/monitor", label: "监控", icon: TrendingUp },
  { href: "/knowledge", label: "知识库", icon: Library },
  { href: "/tools", label: "工具箱", icon: PanelRightOpen },
];

/**
 * MobileNav — 移动端底部导航栏
 *
 * - 固定在屏幕底部
 * - 仅在移动端（<md 断点）显示
 * - 5 个主要入口，带图标和标签
 * - 当前路由高亮（橙色渐变指示器 + 亮度文字）
 * - 使用 lucide-react 图标
 * - 适配 safe-area-inset-bottom 全面屏
 */
export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav
      className={cn(
        "fixed bottom-0 left-0 right-0 z-50",
        "border-t border-white/10",
        "bg-black/80 backdrop-blur-xl",
        "pb-safe-bottom",
        "md:hidden",
        "transition-all duration-300"
      )}
    >
      <div className="flex items-center justify-around h-14 sm:h-16 px-2">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive =
            href === "/"
              ? pathname === "/"
              : pathname.startsWith(href);

          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex flex-col items-center justify-center gap-0.5",
                "relative px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg",
                "transition-all duration-200",
                "active:scale-95 touch-manipulation",
                isActive
                  ? "text-white"
                  : "text-white/40 hover:text-white/60"
              )}
            >
              {/* 活跃指示器 */}
              {isActive && (
                <span className="absolute -top-[5px] left-1/2 -translate-x-1/2 h-0.5 w-6 sm:w-8 rounded-full bg-gradient-to-r from-orange-500 to-pink-500" />
              )}

              {/* 图标 */}
              <Icon
                className={cn(
                  "h-5 w-5 transition-all duration-200",
                  isActive && "drop-shadow-[0_0_6px_rgba(249,115,22,0.4)]"
                )}
              />

              {/* 标签 */}
              <span
                className={cn(
                  "text-[10px] font-medium transition-all duration-200",
                  isActive && "bg-gradient-to-r from-orange-500 to-pink-500 bg-clip-text text-transparent"
                )}
              >
                {label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
