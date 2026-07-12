"use client";

import { Skeleton } from "@/components/skeleton";

export default function GlobalLoading() {
  return (
    <div className="relative">
      {/* 页面内容骨架 */}
      <div className="container space-y-8 py-8">
        {/* 页面标题区域 */}
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>

        {/* 统计卡片行 */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Skeleton variant="card" />
          <Skeleton variant="card" />
          <Skeleton variant="card" />
          <Skeleton variant="card" />
        </div>

        {/* 内容卡片网格 */}
        <div className="space-y-1">
          <Skeleton className="h-6 w-32 mb-4" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Skeleton variant="card" />
            <Skeleton variant="card" />
            <Skeleton variant="card" />
          </div>
        </div>

        {/* 图表区域 */}
        <div className="space-y-1">
          <Skeleton className="h-6 w-32 mb-4" />
          <Skeleton variant="chart" className="h-64" />
        </div>

        {/* 底部文本行 */}
        <div className="space-y-3">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-5/6" />
        </div>
      </div>
    </div>
  );
}
