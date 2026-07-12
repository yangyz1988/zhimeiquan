"use client";

import { Skeleton } from "@/components/skeleton";

export default function DashboardLoading() {
  return (
    <div className="container py-8 space-y-8">
      {/* 欢迎区域 */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-56" />
        <Skeleton className="h-4 w-80" />
      </div>

      {/* 统计卡片网格 */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Skeleton variant="card" />
        <Skeleton variant="card" />
        <Skeleton variant="card" />
        <Skeleton variant="card" />
      </div>

      {/* 图表区域 */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-1">
          <Skeleton className="h-6 w-28 mb-4" />
          <Skeleton variant="chart" className="h-72" />
        </div>
        <div className="space-y-1">
          <Skeleton className="h-6 w-28 mb-4" />
          <Skeleton variant="chart" className="h-72" />
        </div>
      </div>

      {/* 最近活动表格 */}
      <div className="space-y-1">
        <Skeleton className="h-6 w-32 mb-4" />
        <div className="glass-card p-4 space-y-3">
          {Array.from({ length: 5 }, (_, i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-8 w-8 rounded-full" variant="circle" />
              <div className="flex-1 space-y-1">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-3 w-32" />
              </div>
              <Skeleton className="h-6 w-16 rounded-full" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
