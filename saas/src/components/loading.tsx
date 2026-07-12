"use client";

import { Loader2 } from "lucide-react";

interface LoadingProps {
  message?: string;
  size?: "sm" | "md" | "lg";
  fullPage?: boolean;
}

export function Loading({ message = "加载中...", size = "md", fullPage = false }: LoadingProps) {
  const sizeClass = {
    sm: "h-4 w-4",
    md: "h-8 w-8",
    lg: "h-12 w-12",
  }[size];

  const container = (
    <div className="flex flex-col items-center justify-center gap-2 py-8">
      <Loader2 className={`${sizeClass} animate-spin text-orange-500`} />
      <p className="text-sm text-white/50">{message}</p>
    </div>
  );

  if (fullPage) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        {container}
      </div>
    );
  }

  return container;
}

/**
 * @deprecated 请使用 @/components/skeleton 中的 Skeleton 组件
 * 保留此组件以确保向后兼容
 */
export function SkeletonCard() {
  return (
    <div className="space-y-3">
      <div className="h-4 w-3/4 animate-pulse rounded bg-white/10" />
      <div className="h-4 w-1/2 animate-pulse rounded bg-white/10" />
      <div className="h-4 w-5/6 animate-pulse rounded bg-white/10" />
    </div>
  );
}
