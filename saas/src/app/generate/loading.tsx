"use client";

import { Skeleton } from "@/components/skeleton";

export default function GenerateLoading() {
  return (
    <div className="container py-8 space-y-8">
      {/* 页面标题区域 */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-4 w-64" />
      </div>

      {/* 生成表单区域 */}
      <div className="glass-card p-6 space-y-4">
        {/* 平台选择标签 */}
        <div className="flex gap-2">
          <Skeleton className="h-8 w-20 rounded-full" />
          <Skeleton className="h-8 w-20 rounded-full" />
          <Skeleton className="h-8 w-20 rounded-full" />
          <Skeleton className="h-8 w-20 rounded-full" />
        </div>

        {/* 输入区域 */}
        <Skeleton className="h-32 w-full" />

        {/* 生成按钮 */}
        <div className="flex justify-end">
          <Skeleton className="h-10 w-32 rounded-lg" />
        </div>
      </div>

      {/* 结果预览区域 */}
      <div className="space-y-1">
        <Skeleton className="h-6 w-36 mb-4" />
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton variant="card" />
          <Skeleton variant="card" />
        </div>
      </div>

      {/* 历史记录区域 */}
      <div className="space-y-1">
        <Skeleton className="h-6 w-32 mb-4" />
        <div className="space-y-3">
          <Skeleton variant="card" />
          <Skeleton variant="card" />
        </div>
      </div>
    </div>
  );
}
