"use client";

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "card" | "circle" | "chart";
  count?: number;
}

/**
 * Skeleton — 全局骨架屏加载组件
 *
 * 变体:
 * - text:   单行文字占位
 * - card:   卡片布局占位（含标题 + 多行内容）
 * - circle: 圆形头像/图标占位
 * - chart:  图表区域占位
 */
export function Skeleton({ className, variant = "text", count = 1 }: SkeletonProps) {
  const items = Array.from({ length: count }, (_, i) => i);

  const renderItem = (key: number) => {
    switch (variant) {
      case "card":
        return (
          <div
            key={key}
            className={cn(
              "glass-card p-4 space-y-3",
              "animate-pulse",
              className
            )}
          >
            {/* 标题行 */}
            <div className="h-5 w-3/5 rounded-md bg-white/10" />
            {/* 内容行 */}
            <div className="space-y-2">
              <div className="h-3 w-full rounded-sm bg-white/8" />
              <div className="h-3 w-5/6 rounded-sm bg-white/8" />
              <div className="h-3 w-4/6 rounded-sm bg-white/8" />
            </div>
            {/* 底部标签 */}
            <div className="flex gap-2 pt-1">
              <div className="h-5 w-14 rounded-full bg-white/8" />
              <div className="h-5 w-16 rounded-full bg-white/8" />
            </div>
          </div>
        );

      case "circle":
        return (
          <div
            key={key}
            className={cn(
              "rounded-full bg-white/10 animate-pulse",
              "h-12 w-12",
              className
            )}
          />
        );

      case "chart":
        return (
          <div
            key={key}
            className={cn(
              "glass-card p-4 space-y-3 animate-pulse",
              className
            )}
          >
            {/* 图例 */}
            <div className="flex gap-3">
              <div className="h-3 w-16 rounded-sm bg-white/10" />
              <div className="h-3 w-12 rounded-sm bg-white/10" />
              <div className="h-3 w-14 rounded-sm bg-white/10" />
            </div>
            {/* 模拟柱状图 */}
            <div className="flex items-end gap-2 pt-2 h-32">
              {[70, 45, 85, 60, 90, 55, 75].map((h, i) => (
                <div
                  key={i}
                  className="flex-1 rounded-t-sm bg-white/10"
                  style={{ height: `${h}%` }}
                />
              ))}
            </div>
          </div>
        );

      case "text":
      default:
        return (
          <div
            key={key}
            className={cn(
              "h-4 w-full rounded-sm bg-white/10 animate-pulse",
              className
            )}
          />
        );
    }
  };

  // 单行文本可以合并渲染，不放容器
  if (variant === "text" && count <= 1) {
    return (
      <div
        className={cn(
          "h-4 w-full rounded-sm bg-white/10 animate-pulse",
          className
        )}
      />
    );
  }

  return <div className={cn(variant === "card" && "space-y-4")}>{items.map(renderItem)}</div>;
}

/**
 * SkeletonGroup — 方便批量渲染多个 skeleton，支持混合布局
 */
export function SkeletonGroup({
  variant = "text",
  count = 3,
  className,
}: SkeletonProps) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }, (_, i) => (
        <Skeleton key={i} variant={variant} className={className} />
      ))}
    </div>
  );
}

/**
 * PageSkeleton — 整页加载骨架屏，含标题区 + 内容区
 */
export function PageSkeleton() {
  return (
    <div className="space-y-6 p-6">
      {/* 页面标题 */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-72" />
      </div>
      {/* 统计卡片行 */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} variant="card" />
        ))}
      </div>
      {/* 图表区 */}
      <Skeleton variant="chart" className="h-72" />
    </div>
  );
}
