"use client";

import Link from "next/link";
import { Zap } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t bg-muted/30">
      <div className="container py-12">
        <div className="grid gap-8 md:grid-cols-4">
          {/* Brand */}
          <div>
            <Link href="/" className="flex items-center space-x-2 mb-3">
              <Zap className="h-5 w-5 text-orange-500" />
              <span className="font-bold">智媒圈</span>
            </Link>
            <p className="text-sm text-muted-foreground">
              AI内容策略引擎<br />让每个人都能用AI做出爆款内容
            </p>
          </div>
          {/* Product */}
          <div>
            <h4 className="mb-3 text-sm font-semibold">产品</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link href="/generate" className="hover:text-foreground">AI生成引擎</Link></li>
              <li><Link href="/monitor" className="hover:text-foreground">爆款监控</Link></li>
              <li><Link href="/analytics" className="hover:text-foreground">数据分析</Link></li>
              <li><Link href="/tools" className="hover:text-foreground">工具箱</Link></li>
            </ul>
          </div>
          {/* Resources */}
          <div>
            <h4 className="mb-3 text-sm font-semibold">资源</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link href="/knowledge" className="hover:text-foreground">九层知识体系</Link></li>
              <li><Link href="/experts" className="hover:text-foreground">专家引擎</Link></li>
              <li><Link href="/operations" className="hover:text-foreground">运营中心</Link></li>
              <li><Link href="/pricing" className="hover:text-foreground">会员定价</Link></li>
            </ul>
          </div>
          {/* About */}
          <div>
            <h4 className="mb-3 text-sm font-semibold">关于</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><span>关于我们</span></li>
              <li><span>联系我们</span></li>
              <li><span>API 文档</span></li>
            </ul>
          </div>
        </div>
        <div className="mt-8 border-t pt-6 text-center text-xs text-muted-foreground">
          &copy; 2026 智媒圈 - AI内容策略引擎 · 让每个人都能用AI做出爆款内容
        </div>
      </div>
    </footer>
  );
}
