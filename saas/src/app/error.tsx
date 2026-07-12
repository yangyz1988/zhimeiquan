"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    console.error("页面渲染错误:", error);
  }, [error]);

  return (
    <div className="relative flex min-h-[80vh] flex-col items-center justify-center px-4 text-center">
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute -top-40 right-1/4 w-[500px] h-[500px] rounded-full bg-orange-500/[0.05] blur-[120px]" />
        <div className="absolute bottom-0 left-1/3 w-[400px] h-[400px] rounded-full bg-red-500/[0.04] blur-[100px]" />
      </div>

      <div className="relative z-10 flex flex-col items-center gap-6">
        <div className="relative">
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-red-500/10 border border-red-500/20">
            <AlertTriangle className="h-9 w-9 text-orange-400" />
          </div>
          <div className="absolute -inset-4 rounded-full bg-orange-500/[0.06] blur-[40px]" />
        </div>

        <div className="space-y-2">
          <h2 className="text-xl sm:text-2xl font-bold text-white">页面加载出错</h2>
          <p className="text-sm sm:text-base text-white/50 max-w-md">
            抱歉，页面渲染时发生了意外错误。请重试，如果问题持续存在请联系支持。
          </p>
        </div>

        {error.message && (
          <div className="border border-red-500/10 bg-white/[0.02] backdrop-blur-sm rounded-lg p-3 max-w-md w-full">
            <p className="text-xs text-white/30 uppercase tracking-wider mb-1">错误详情</p>
            <p className="text-sm text-white/50 font-mono break-all">{error.message}</p>
            {error.digest && (
              <p className="text-xs text-white/20 mt-1 font-mono">Digest: {error.digest}</p>
            )}
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={reset}
            className="inline-flex items-center justify-center gap-2 rounded-md bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600 text-white font-medium px-6 py-3 text-sm"
          >
            <RefreshCw className="h-4 w-4" />
            重试
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center gap-2 rounded-md border border-white/15 text-white/70 hover:bg-white/10 font-medium px-6 py-3 text-sm"
          >
            返回首页
          </a>
        </div>
      </div>
    </div>
  );
}
