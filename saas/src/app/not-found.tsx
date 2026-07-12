import Link from "next/link";
import { Home, ArrowLeft, Search } from "lucide-react";

export default function NotFound() {
  return (
    <div className="relative flex min-h-[80vh] flex-col items-center justify-center px-4 text-center">
      {/* Background glow */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute -top-40 right-1/4 w-[500px] h-[500px] rounded-full bg-orange-500/[0.05] blur-[120px]" />
        <div className="absolute bottom-0 left-1/3 w-[400px] h-[400px] rounded-full bg-purple-500/[0.04] blur-[100px]" />
      </div>

      <div className="relative z-10 flex flex-col items-center gap-6">
        <div className="relative">
          <h1 className="text-[120px] sm:text-[160px] font-black leading-none tracking-tighter bg-gradient-to-r from-orange-400 to-pink-500 bg-clip-text text-transparent select-none">
            404
          </h1>
          <div className="absolute -inset-4 rounded-full bg-orange-500/[0.08] blur-[60px]" />
        </div>

        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/5 border border-white/10">
          <Search className="h-7 w-7 text-orange-400" />
        </div>

        <div className="space-y-2">
          <h2 className="text-xl sm:text-2xl font-bold text-white">页面未找到</h2>
          <p className="text-sm sm:text-base text-white/50 max-w-md">
            你访问的页面可能已被移动、删除，或者链接地址有误。
          </p>
        </div>

        <div className="flex items-center gap-3 w-48">
          <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <Link href="/"
            className="inline-flex items-center justify-center gap-2 rounded-md bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600 text-white font-medium px-6 py-3 text-sm"
          >
            <Home className="h-4 w-4" />
            返回首页
          </Link>
          <Link href="/"
            className="inline-flex items-center justify-center gap-2 rounded-md border border-white/15 text-white/70 hover:bg-white/10 font-medium px-6 py-3 text-sm"
          >
            <ArrowLeft className="h-4 w-4" />
            返回上页
          </Link>
        </div>

        <div className="border border-white/5 bg-white/[0.02] backdrop-blur-sm rounded-lg p-4 max-w-sm w-full">
          <p className="text-xs text-white/40 uppercase tracking-wider mb-3">你可能想找</p>
          <div className="grid grid-cols-2 gap-2 text-left">
            <Link href="/generate" className="text-sm text-white/60 hover:text-orange-400 transition-colors">内容生成</Link>
            <Link href="/monitor" className="text-sm text-white/60 hover:text-orange-400 transition-colors">爆款监控</Link>
            <Link href="/knowledge" className="text-sm text-white/60 hover:text-orange-400 transition-colors">知识体系</Link>
            <Link href="/pricing" className="text-sm text-white/60 hover:text-orange-400 transition-colors">会员方案</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
