"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Zap, BarChart3, RefreshCw, ArrowRight, Users, Star, Trophy,
  Crown, Shield, BookOpen, Lightbulb,
} from "lucide-react";
import { PageBackground } from "@/components/ui/page-layout";

const stats = [
  { value: "5,382", label: "人在线", icon: Users },
  { value: "42,856", label: "今日已生成", icon: Zap },
  { value: "4.9", label: "满意度", icon: Star },
  { value: "12,847", label: "用户", icon: Trophy },
];

const engines = [
  { icon: Zap, title: "爆款生成引擎", desc: "输入关键词，30秒生成完整爆款内容", href: "/generate", glow: "glow-orange", iconColor: "text-orange-400" },
  { icon: BarChart3, title: "对标拆解引擎", desc: "粘贴爆款内容，逆向拆解底层方法论", href: "/tools", glow: "glow-blue", iconColor: "text-blue-400" },
  { icon: RefreshCw, title: "自动改写引擎", desc: "低分内容自动优化重写至95+ Fire Score", href: "/generate", glow: "glow-green", iconColor: "text-green-400" },
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

/* -------------------------------------------------------- */
/*  子组件：统计卡片                                          */
/* -------------------------------------------------------- */

function StatCard({ value, label, icon: Icon }: { value: string; label: string; icon: React.ElementType }) {
  return (
    <Card className="glass-card glow-orange text-center">
      <CardContent className="flex flex-col items-center gap-1 py-4">
        <Icon className="h-4 w-4 text-orange-400" />
        <span className="text-xl font-bold text-white">{value}</span>
        <span className="text-xs text-white/40">{label}</span>
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
      <section className="relative flex min-h-[85vh] flex-col items-center justify-center gap-6 overflow-hidden py-20 text-center">
        <PageBackground
          color1="bg-orange-500/[0.06]"
          color2="bg-purple-500/[0.06]"
        />
        <div className="pointer-events-none absolute inset-0 z-0">
          <div className="absolute top-1/3 right-1/3 h-[350px] w-[350px] rounded-full bg-blue-500/[0.04] blur-[80px]" />
        </div>

        <Badge variant="secondary" className="relative z-10 gap-2 border border-white/10 bg-black/30 backdrop-blur-sm">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-orange-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-orange-500" />
          </span>
          爆款公式实时进化中 · 已迭代 1,247 次
        </Badge>

        <h1 className="relative z-10 max-w-3xl text-4xl font-bold tracking-tighter text-white sm:text-5xl lg:text-6xl">
          输入关键词，
          <span className="text-gradient font-black">30秒</span>
          生成可发布赚钱内容
        </h1>

        <p className="relative z-10 max-w-2xl text-lg text-white/50">
          基于九层知识体系 + 50+专家智能体，覆盖13个主流平台
        </p>

        <div className="relative z-10 mx-auto grid grid-cols-2 gap-4 md:grid-cols-4" style={{ maxWidth: 700 }}>
          {stats.map((s) => (
            <StatCard key={s.label} value={s.value} label={s.label} icon={s.icon} />
          ))}
        </div>

        <div className="relative z-10 flex gap-4">
          <Link href="/generate">
            <Button size="lg" className="bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600">
              免费开始创作
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          <Link href="/pricing">
            <Button variant="outline" size="lg" className="border-white/15 text-white/70 hover:bg-white/10">
              查看会员方案
            </Button>
          </Link>
        </div>
      </section>

      {/* ---- 三大核心引擎 ---- */}
      <section className="container space-y-12 py-16">
        <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">三大核心引擎</h2>
        <p className="text-center text-white/40">爆款内容从这里开始</p>
        <div className="grid gap-6 md:grid-cols-3">
          {engines.map((e) => (
            <Link key={e.title} href={e.href}>
              <Card className={`glass-card ${e.glow} group cursor-pointer transition-all duration-300 hover:scale-[1.02]`}>
                <CardHeader>
                  <e.icon className={`mb-2 h-8 w-8 ${e.iconColor} transition-transform group-hover:scale-110`} />
                  <CardTitle className="text-white">{e.title}</CardTitle>
                  <CardDescription className="text-white/50">{e.desc}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* ---- 九层知识体系预览 ---- */}
      <section className="container space-y-12 py-16">
        <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">九层知识体系</h2>
        <p className="text-center text-white/40">从底层逻辑到顶层运营</p>
        <div className="mx-auto grid max-w-3xl gap-4">
          {layers.map((l, i) => (
            <Card key={l.level} className={`glass-card ${l.glow} transition-all duration-300 hover:scale-[1.015]`} style={{ marginTop: i > 0 ? -8 : 0 }}>
              <CardContent className="flex items-center gap-4 py-4">
                <l.icon className={`h-5 w-5 ${l.text}`} />
                <span className={`text-sm font-bold ${l.text}`}>{l.level}</span>
                <span className="text-sm font-semibold text-white">{l.title}</span>
                <span className="ml-auto text-sm text-white/40">{l.desc}</span>
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="mt-8 text-center">
          <Link href="/knowledge">
            <Button variant="outline" className="border-white/15 text-white/70 hover:bg-white/10">
              查看完整体系
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* ---- 用户路径 ---- */}
      <section className="container space-y-12 py-16">
        <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">你现在处在哪一步？</h2>
        <div className="grid gap-6 md:grid-cols-3">
          {paths.map((p) => (
            <Link key={p.title} href={p.href}>
              <Card className={`glass-card ${p.glow} group cursor-pointer transition-all duration-300 hover:scale-[1.02]`}>
                <CardHeader>
                  <div className="mb-1 flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-lg text-2xl" style={{ background: "rgba(255,255,255,0.05)" }}>
                      {p.emoji}
                    </span>
                    <CardTitle className="text-white">{p.title}</CardTitle>
                  </div>
                  <CardDescription className="text-white/50">{p.desc}</CardDescription>
                  <Badge className="mt-2 w-fit border border-white/10 bg-white/5 text-white/70">{p.badge}</Badge>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* ---- Footer CTA ---- */}
      <section className="relative overflow-hidden py-20 text-center">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-orange-500/[0.04] to-transparent" />
        <div className="relative container space-y-3">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">开始用 AI 赚钱</h2>
          <p className="text-white/40">加入 12,847+ 创作者，让爆款不再是玄学</p>
          <div className="flex justify-center gap-4">
            <Link href="/generate">
              <Button size="lg" className="bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600">
                免费开始
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/pricing">
              <Button variant="outline" size="lg" className="border-white/15 text-white/70 hover:bg-white/10">
                查看定价
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
