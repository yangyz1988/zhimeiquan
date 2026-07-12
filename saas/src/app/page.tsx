"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Zap, BarChart3, RefreshCw, ArrowRight, Shield, Star,
  Crown, BookOpen, Lightbulb, TrendingUp, Target, Eye,
} from "lucide-react";
import { PageBackground } from "@/components/ui/page-layout";

const stats = [
  { value: "13", label: "平台覆盖", icon: Zap },
  { value: "50+", label: "专家智能体", icon: Star },
  { value: "95%+", label: "爆款概率", icon: Shield },
  { value: "12+", label: "核心能力", icon: BarChart3 },
];

const engines = [
  { icon: Zap, title: "爆款规则引擎", desc: "实时监控13个平台的爆款规律，AI分析标题模式、钩子类型、算法变化", href: "/monitor", glow: "glow-orange", iconColor: "text-orange-400" },
  { icon: BarChart3, title: "AI 内容工场", desc: "基于平台爆款规则，生成各平台专属的标题/脚本/图文内容", href: "/generate", glow: "glow-blue", iconColor: "text-blue-400" },
  { icon: RefreshCw, title: "数据闭环优化", desc: "发布→采集→评分→分析→优化→再发布，内容越做越爆", href: "/analytics", glow: "glow-green", iconColor: "text-green-400" },
];

const layers = [
  { level: "L9", title: "专家智能体", desc: "50+专家", icon: Crown, text: "text-purple-400", glow: "glow-purple" },
  { level: "L6", title: "爆款概率保障", desc: "95%+", icon: Shield, text: "text-blue-400", glow: "glow-blue" },
  { level: "L3", title: "六大方法论", desc: "反常识+人性...", icon: BookOpen, text: "text-green-400", glow: "glow-green" },
  { level: "L1", title: "爆款底层逻辑", desc: "CTR公式", icon: Lightbulb, text: "text-amber-400", glow: "glow-orange" },
];

const paths = [
  { emoji: "🟢", title: "我是小白", desc: "不会做内容", href: "/generate", badge: "简单方案", glow: "glow-green" },
  { emoji: "🟡", title: "我会做但不赚钱", desc: "没变现路径", href: "/experts", badge: "我要赚钱", glow: "glow-orange" },
  { emoji: "🔴", title: "我要自动化矩阵", desc: "批量做号", href: "/operations", badge: "高级模式", glow: "glow-pink" },
];

const chinaPlatformItems = [
  { icon: TrendingUp, title: "13个中国平台", desc: "抖音、小红书、B站、快手、视频号、公众号、微博、知乎、头条、百度热搜 + 3个国际平台", glow: "glow-orange" },
  { icon: Target, title: "平台算法透视", desc: "每个平台的完播率/收藏率/互动率指标、冷启动窗口、CES评分模型——不是通用建议，是精确数据", glow: "glow-blue" },
  { icon: Eye, title: "实时热点追踪", desc: "Playwright 浏览器自动化实时采集各平台热搜，AI 分析后生成可执行的标题/钩子建议", glow: "glow-green" },
];

const comparisonRows = [
  { label: "AI 内容生成", values: ["⭐⭐⭐⭐⭐", "⭐⭐⭐", "❌", "⭐⭐⭐⭐"] },
  { label: "平台爆款规则分析", values: ["❌", "❌", "⭐⭐", "⭐⭐⭐⭐⭐"] },
  { label: "多平台内容分发", values: ["❌", "⭐⭐⭐⭐⭐", "❌", "⭐⭐⭐⭐"] },
  { label: "竞品内容监控", values: ["❌", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐", "⭐⭐⭐⭐"] },
  { label: "内容质量评分", values: ["⭐", "⭐⭐", "⭐⭐", "⭐⭐⭐⭐⭐"] },
  { label: "数据闭环优化", values: ["⭐⭐", "⭐⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐⭐"] },
  { label: "中国市场适配", values: ["⭐⭐", "⭐", "⭐", "⭐⭐⭐⭐⭐"] },
];

/* -------------------------------------------------------- */
/*  子组件：统计卡片                                          */
/* -------------------------------------------------------- */

function StatCard({ value, label, icon: Icon }: { value: string; label: string; icon: React.ElementType }) {
  return (
    <Card className="glass-card glow-orange text-center">
      <CardContent className="flex flex-col items-center gap-0.5 py-3 sm:gap-1 sm:py-4">
        <Icon className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-orange-400" />
        <span className="text-lg sm:text-xl font-bold text-white">{value}</span>
        <span className="text-[10px] sm:text-xs text-white/40">{label}</span>
      </CardContent>
    </Card>
  );
}

/* -------------------------------------------------------- */
/*  落地页                                                   */
/* -------------------------------------------------------- */

export default function Home() {
  return (
    <div className="flex flex-col">
      {/* ---- Hero: 全屏光晕 + 大气排版 ---- */}
      <section className="relative flex min-h-[70vh] sm:min-h-[80vh] lg:min-h-[85vh] flex-col items-center justify-center gap-4 sm:gap-6 overflow-hidden px-4 py-16 sm:py-20 text-center">
        <PageBackground
          color1="bg-orange-500/[0.06]"
          color2="bg-purple-500/[0.06]"
        />
        <div className="pointer-events-none absolute inset-0 z-0">
          <div className="absolute top-1/4 sm:top-1/3 right-1/4 sm:right-1/3 h-[200px] w-[200px] sm:h-[300px] sm:w-[300px] lg:h-[350px] lg:w-[350px] rounded-full bg-blue-500/[0.04] blur-[80px]" />
        </div>

        <Badge variant="secondary" className="relative z-10 gap-2 border border-white/10 bg-black/30 backdrop-blur-sm text-[11px] sm:text-sm">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-orange-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-orange-500" />
          </span>
          <span className="hidden sm:inline">13平台爆款规则实时进化中 · 已分析 50,000+ 爆款内容</span>
          <span className="sm:hidden">13平台爆款规则实时进化中</span>
        </Badge>

        <h1 className="relative z-10 max-w-3xl text-2xl font-bold tracking-tighter text-white sm:text-4xl md:text-5xl lg:text-6xl">
          不用猜算法想标题，
          <span className="text-gradient font-black">让 AI 替你分析爆款规则</span>
        </h1>

        <p className="relative z-10 max-w-2xl text-sm sm:text-base md:text-lg text-white/50 px-2 sm:px-0">
          不是通用 AI 写作工具，而是基于13个平台真实爆款数据的<span className="text-white/70 font-medium">内容策略引擎</span>——告诉你每个平台现在什么最火、怎么写更爆
        </p>

        <div className="relative z-10 mx-auto grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-4" style={{ maxWidth: 700 }}>
          {stats.map((s) => (
            <StatCard key={s.label} value={s.value} label={s.label} icon={s.icon} />
          ))}
        </div>

        <div className="relative z-10 flex flex-col sm:flex-row gap-3 sm:gap-4">
          <Link href="/generate">
            <Button size="lg" className="bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600 w-full sm:w-auto">
              免费开始创作
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          <Link href="/pricing">
            <Button variant="outline" size="lg" className="border-white/15 text-white/70 hover:bg-white/10 w-full sm:w-auto">
              查看会员方案
            </Button>
          </Link>
        </div>
      </section>

      {/* ---- 三大核心引擎 ---- */}
      <section className="container space-y-8 sm:space-y-12 px-4 sm:px-6 py-12 sm:py-16">
        <h2 className="text-center text-2xl sm:text-3xl md:text-4xl font-bold">
          <span className="text-white">不止是 AI 写作</span>{" "}
          <span className="text-gradient">而是爆款策略引擎</span>
        </h2>
        <p className="text-center text-white/40 text-sm sm:text-base">
          市面上的 AI 写作工具只帮你"写出来"，我们帮你"写爆款"
        </p>
        <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {engines.map((e) => (
            <Link key={e.title} href={e.href}>
              <Card className={`glass-card ${e.glow} group cursor-pointer transition-all duration-300 hover:scale-[1.02]`}>
                <CardHeader>
                  <e.icon className={`mb-2 h-7 w-7 sm:h-8 sm:w-8 ${e.iconColor} transition-transform group-hover:scale-110`} />
                  <CardTitle className="text-white text-base sm:text-lg">{e.title}</CardTitle>
                  <CardDescription className="text-white/50 text-sm">{e.desc}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* ---- 九层知识体系预览 ---- */}
      <section className="container space-y-8 sm:space-y-12 px-4 sm:px-6 py-12 sm:py-16">
        <h2 className="text-center text-2xl sm:text-3xl md:text-4xl font-bold text-white">九层知识体系</h2>
        <p className="text-center text-white/40 text-sm sm:text-base">从底层逻辑到顶层运营</p>
        <div className="mx-auto grid max-w-3xl gap-3 sm:gap-4">
          {layers.map((l, i) => (
            <Card key={l.level} className={`glass-card ${l.glow} transition-all duration-300 hover:scale-[1.015]`} style={{ marginTop: i > 0 ? -8 : 0 }}>
              <CardContent className="flex items-center gap-3 sm:gap-4 py-3 sm:py-4">
                <l.icon className={`h-4 w-4 sm:h-5 sm:w-5 ${l.text} shrink-0`} />
                <span className={`text-xs sm:text-sm font-bold ${l.text} shrink-0`}>{l.level}</span>
                <span className="text-xs sm:text-sm font-semibold text-white truncate">{l.title}</span>
                <span className="ml-auto text-xs sm:text-sm text-white/40 hidden xs:inline shrink-0">{l.desc}</span>
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="mt-6 sm:mt-8 text-center">
          <Link href="/knowledge">
            <Button variant="outline" className="border-white/15 text-white/70 hover:bg-white/10">
              查看完整体系
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* ---- 用户路径 ---- */}
      <section className="container space-y-8 sm:space-y-12 px-4 sm:px-6 py-12 sm:py-16">
        <h2 className="text-center text-2xl sm:text-3xl md:text-4xl font-bold text-white">你现在处在哪一步？</h2>
        <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {paths.map((p) => (
            <Link key={p.title} href={p.href}>
              <Card className={`glass-card ${p.glow} group cursor-pointer transition-all duration-300 hover:scale-[1.02]`}>
                <CardHeader>
                  <div className="mb-1 flex items-center gap-3">
                    <span className="flex h-9 w-9 sm:h-10 sm:w-10 items-center justify-center rounded-lg text-xl sm:text-2xl" style={{ background: "rgba(255,255,255,0.05)" }}>
                      {p.emoji}
                    </span>
                    <CardTitle className="text-white text-base sm:text-lg">{p.title}</CardTitle>
                  </div>
                  <CardDescription className="text-white/50 text-sm">{p.desc}</CardDescription>
                  <Badge className="mt-2 w-fit border border-white/10 bg-white/5 text-white/70 text-xs">{p.badge}</Badge>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* ---- 中国平台深耕 ---- */}
      <section className="container space-y-8 sm:space-y-12 px-4 sm:px-6 py-12 sm:py-16">
        <h2 className="text-center text-2xl sm:text-3xl md:text-4xl font-bold text-white">专为中国内容创作者打造</h2>
        <p className="text-center text-white/40 text-sm sm:text-base">不是翻译自英文工具的"汉化版"，而是从零开始深耕中国平台</p>
        <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {chinaPlatformItems.map((item) => (
            <Card key={item.title} className={`glass-card ${item.glow}`}>
              <CardHeader>
                <item.icon className="mb-2 h-7 w-7 sm:h-8 sm:w-8 text-orange-400" />
                <CardTitle className="text-white text-base sm:text-lg">{item.title}</CardTitle>
                <CardDescription className="text-white/50 text-sm">{item.desc}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      {/* ---- 竞品差异化 ---- */}
      <section className="container space-y-8 sm:space-y-12 px-4 sm:px-6 py-12 sm:py-16">
        <h2 className="text-center text-2xl sm:text-3xl md:text-4xl font-bold text-white">
          为什么选择<span className="text-gradient">智媒圈</span>？
        </h2>
        <div className="mx-auto max-w-4xl overflow-x-auto -mx-4 sm:mx-auto scrollbar-thin">
          <table className="w-full text-left text-xs sm:text-sm min-w-[640px]">
            <thead>
              <tr className="border-b border-white/10 text-white/60">
                <th className="py-3 pr-2 sm:pr-4 font-medium text-left">能力维度</th>
                <th className="py-3 px-2 sm:px-3 text-center font-medium whitespace-nowrap">AI写作<br /><span className="text-[10px] sm:text-xs text-white/30">(Jasper/Copy.ai)</span></th>
                <th className="py-3 px-2 sm:px-3 text-center font-medium whitespace-nowrap">社媒管理<br /><span className="text-[10px] sm:text-xs text-white/30">(Sprout Social)</span></th>
                <th className="py-3 px-2 sm:px-3 text-center font-medium whitespace-nowrap">竞品监控<br /><span className="text-[10px] sm:text-xs text-white/30">(BuzzSumo)</span></th>
                <th className="py-3 pl-2 sm:pl-3 text-center font-medium text-orange-400 whitespace-nowrap">智媒圈</th>
              </tr>
            </thead>
            <tbody className="text-white/60">
              {comparisonRows.map((row) => (
                <tr key={row.label} className="border-b border-white/5 hover:bg-white/[0.02]">
                  <td className="py-2.5 sm:py-3 pr-2 sm:pr-4 font-medium text-white/70">{row.label}</td>
                  {row.values.map((v, i) => (
                    <td key={i} className={`py-2.5 sm:py-3 px-2 sm:px-3 text-center ${i === row.values.length - 1 ? "text-orange-400 font-medium" : ""}`}>
                      {v}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ---- Footer CTA ---- */}
      <section className="relative overflow-hidden py-16 sm:py-20 text-center px-4">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-orange-500/[0.04] to-transparent" />
        <div className="relative container space-y-3">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white">不再凭感觉做内容</h2>
          <p className="text-white/40 text-sm sm:text-base">用数据和 AI，让每一条内容都有爆款基因</p>
          <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4 pt-2">
            <Link href="/generate">
              <Button size="lg" className="bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600 w-full sm:w-auto">
                免费开始
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/pricing">
              <Button variant="outline" size="lg" className="border-white/15 text-white/70 hover:bg-white/10 w-full sm:w-auto">
                查看定价
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
