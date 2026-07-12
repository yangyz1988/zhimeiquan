"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Inbox } from "lucide-react";
import type { ElementType } from "react";

interface EmptyStateProps {
  /** 图标组件（lucide-react 图标） */
  icon?: ElementType;
  /** 主标题 */
  title: string;
  /** 副标题/描述文字 */
  description?: string;
  /** 可选的操作按钮 */
  action?: {
    label: string;
    onClick: () => void;
    variant?: "default" | "outline" | "secondary" | "ghost" | "destructive" | "link";
  };
  /** 自定义类名 */
  className?: string;
  /** 紧凑模式（减少内边距） */
  compact?: boolean;
}

/**
 * EmptyState — 空数据展示组件
 *
 * 在数据列表、搜索结果、筛选结果等为空时展示友好的提示信息。
 * 支持自定义图标、标题、描述和操作按钮。
 *
 * @example
 * ```tsx
 * <EmptyState
 *   icon={SearchX}
 *   title="未找到结果"
 *   description="请尝试更换搜索关键词"
 *   action={{ label: "清除筛选", onClick: () => setFilter("") }}
 * />
 * ```
 */
export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  className,
  compact = false,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center",
        "glass-card border border-white/10",
        compact ? "p-6" : "p-8 sm:p-12",
        "transition-all duration-300",
        className
      )}
    >
      {/* 图标容器 */}
      <div className={cn(
        "mb-4 flex items-center justify-center",
        "rounded-full bg-white/[0.05]",
        compact ? "h-10 w-10" : "h-14 w-14 sm:h-16 sm:w-16"
      )}>
        <Icon className={cn(
          "text-white/40",
          compact ? "h-5 w-5" : "h-7 w-7 sm:h-8 sm:w-8"
        )} />
      </div>

      {/* 标题 */}
      <h3 className={cn(
        "font-semibold text-white",
        compact ? "text-sm" : "text-base sm:text-lg"
      )}>
        {title}
      </h3>

      {/* 描述 */}
      {description && (
        <p className={cn(
          "mt-1 text-white/50 max-w-xs",
          compact ? "text-xs" : "text-sm"
        )}>
          {description}
        </p>
      )}

      {/* 操作按钮 */}
      {action && (
        <Button
          variant={action.variant || "outline"}
          size="sm"
          onClick={action.onClick}
          className={cn(
            "mt-4",
            "border-white/10 text-white/70 hover:text-white hover:bg-white/10"
          )}
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}
