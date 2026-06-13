"use client";

import Link from "next/link";
import { Zap } from "lucide-react";

export function Footer() {
  return (
    <footer className="relative border-t border-white/5">
      {/* Subtle grid background */}
      <div className="absolute inset-0 bg-grid pointer-events-none" />

      <div className="container relative py-16">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div>
            <Link href="/" className="flex items-center gap-2 mb-4">
              <Zap className="h-6 w-6 text-orange-500" />
              <span className="text-xl font-bold">智媒圈</span>
            </Link>
            <p className="text-sm text-white/40 max-w-xs leading-relaxed">
              AI内容策略引擎<br />让每个人都能用AI做出爆款内容
            </p>
          </div>

          <div>
            <h4 className="mb-4 text-sm font-semibold text-white/60">产品</h4>
            <ul className="space-y-3">
              {["AI生成引擎", "爆款监控", "数据分析", "工具箱"].map((item) => (
                <li key={item}>
                  <span className="text-sm text-white/30 hover:text-orange-400 transition-colors cursor-pointer">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="mb-4 text-sm font-semibold text-white/60">资源</h4>
            <ul className="space-y-3">
              {["九层知识体系", "专家引擎", "运营中心", "会员定价"].map((item) => (
                <li key={item}>
                  <span className="text-sm text-white/30 hover:text-purple-400 transition-colors cursor-pointer">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="mb-4 text-sm font-semibold text-white/60">关于</h4>
            <ul className="space-y-3">
              {["关于我们", "联系我们", "API 文档"].map((item) => (
                <li key={item}>
                  <span className="text-sm text-white/30 hover:text-cyan-400 transition-colors cursor-pointer">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-6 border-t border-white/5 text-center text-xs text-white/20">
          &copy; 2026 智媒圈 - AI内容策略引擎 · 让每个人都能用AI做出爆款内容
        </div>
      </div>
    </footer>
  );
}
