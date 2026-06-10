"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Zap,
  BarChart3,
  RefreshCw,
  ArrowRight,
  Flame,
  Users,
  Star,
  Trophy,
  Crown,
  Shield,
  BookOpen,
  Lightbulb,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/*  Hero Section                                                       */
/* ------------------------------------------------------------------ */

const stats = [
  { value: "5,382", label: "人在线", icon: Users },
  { value: "42,856", label: "今日已生成", icon: Zap },
  { value: "4.9", label: "满意度", icon: Star },
  { value: "12,847", label: "用户", icon: Trophy },
];

/* ------------------------------------------------------------------ */
/*  Three Core Engines                                                 */
/* ------------------------------------------------------------------ */

const engines = [
  {
    icon: Zap,
    title: "爆款生成引擎",
    desc: "输入关键词，30秒生成完整爆款内容",
    href: "/generate",
    border: "border-t-orange-500",
  },
  {
    icon: BarChart3,
    title: "对标拆解引擎",
    desc: "粘贴爆款内容，逆向拆解底层方法论",
    href: "/tools",
    border: "border-t-blue-500",
  },
  {
    icon: RefreshCw,
    title: "自动改写引擎",
    desc: "低分内容自动优化重写至95+ Fire Score",
    href: "/generate",
    border: "border-t-green-500",
  },
];

/* ------------------------------------------------------------------ */
/*  Nine-Layer Knowledge Preview                                       */
/* ------------------------------------------------------------------ */

const layers = [
  {
    level: "L9",
    title: "专家智能体",
    desc: "50+专家",
    icon: Crown,
    border: "border-l-purple-500",
    text: "text-purple-600",
  },
  {
    level: "L6",
    title: "爆款概率保障",
    desc: "95%+",
    icon: Shield,
    border: "border-l-blue-500",
    text: "text-blue-600",
  },
  {
    level: "L3",
    title: "六大方法论",
    desc: "反常识+人性...",
    icon: BookOpen,
    border: "border-l-green-500",
    text: "text-green-600",
  },
  {
    level: "L1",
    title: "爆款底层逻辑",
    desc: "CTR公式",
    icon: Lightbulb,
    border: "border-l-amber-500",
    text: "text-amber-600",
  },
];

/* ------------------------------------------------------------------ */
/*  User Path                                                          */
/* ------------------------------------------------------------------ */

const paths = [
  {
    emoji: "🟢",
    title: "我是小白",
    desc: "不会做内容",
    href: "/generate",
    badge: "简单方案",
    badgeVariant: "default" as const,
  },
  {
    emoji: "🟡",
    title: "我会做但不赚钱",
    desc: "没变现路径",
    href: "/experts",
    badge: "我要赚钱",
    badgeVariant: "secondary" as const,
  },
  {
    emoji: "🔴",
    title: "我要自动化矩阵",
    desc: "批量做号",
    href: "/operations",
    badge: "高级模式",
    badgeVariant: "destructive" as const,
  },
];

/* ------------------------------------------------------------------ */
/*  Page Component                                                     */
/* ------------------------------------------------------------------ */

export default function Home() {
  return (
    <div className="flex flex-col">
      {/* -------- Hero -------- */}
      <section className="container flex flex-col items-center gap-6 py-20 text-center">
        <Badge variant="secondary" className="gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-orange-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-orange-500" />
          </span>
          爆款公式实时进化中 · 已迭代 1,247 次
        </Badge>

        <h1 className="max-w-3xl text-4xl font-bold tracking-tighter sm:text-5xl lg:text-6xl">
          输入关键词，
          <span className="text-orange-500 font-black">30秒</span>
          生成可发布赚钱内容
        </h1>

        <p className="max-w-2xl text-lg text-muted-foreground">
          基于九层知识体系 + 50+专家智能体，覆盖13个主流平台
        </p>

        {/* Stats Row */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4" style={{ maxWidth: 700 }}>
          {stats.map((s) => (
            <Card key={s.label} className="text-center">
              <CardContent className="flex flex-col items-center gap-1 py-4">
                <s.icon className="h-4 w-4 text-orange-500" />
                <span className="text-xl font-bold">{s.value}</span>
                <span className="text-xs text-muted-foreground">{s.label}</span>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* CTA */}
        <div className="flex gap-4">
          <Link href="/generate">
            <Button size="lg">
              免费开始创作
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          <Link href="/pricing">
            <Button variant="outline" size="lg">
              查看会员方案
            </Button>
          </Link>
        </div>
      </section>

      {/* -------- Three Core Engines -------- */}
      <section className="container py-12">
        <h2 className="mb-8 text-center text-3xl font-bold">三大核心引擎</h2>
        <div className="grid gap-6 md:grid-cols-3">
          {engines.map((e) => (
            <Link key={e.title} href={e.href}>
              <Card className={`border-t-4 ${e.border} transition-shadow hover:shadow-md h-full`}>
                <CardHeader>
                  <e.icon className="mb-2 h-8 w-8 text-orange-500" />
                  <CardTitle>{e.title}</CardTitle>
                  <CardDescription>{e.desc}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* -------- Nine-Layer Knowledge Preview -------- */}
      <section className="container py-12">
        <h2 className="mb-2 text-center text-3xl font-bold">九层知识体系</h2>
        <p className="mb-8 text-center text-muted-foreground">从底层逻辑到顶层运营</p>
        <div className="mx-auto grid max-w-3xl gap-4">
          {layers.map((l) => (
            <Card key={l.level} className={`border-l-4 ${l.border}`}>
              <CardContent className="flex items-center gap-4 py-4">
                <l.icon className={`h-5 w-5 ${l.text}`} />
                <span className={`text-sm font-bold ${l.text}`}>{l.level}</span>
                <span className="text-sm font-semibold">{l.title}</span>
                <span className="ml-auto text-sm text-muted-foreground">{l.desc}</span>
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="mt-6 text-center">
          <Link href="/knowledge">
            <Button variant="outline">
              查看完整体系
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* -------- User Path -------- */}
      <section className="container py-12">
        <h2 className="mb-8 text-center text-3xl font-bold">你现在处在哪一步？</h2>
        <div className="grid gap-6 md:grid-cols-3">
          {paths.map((p) => (
            <Link key={p.title} href={p.href}>
              <Card className="transition-shadow hover:shadow-md h-full">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>
                      <span className="mr-2">{p.emoji}</span>
                      {p.title}
                    </CardTitle>
                    <Badge variant={p.badgeVariant}>{p.badge}</Badge>
                  </div>
                  <CardDescription>{p.desc}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* -------- Footer CTA -------- */}
      <section className="container py-16 text-center">
        <h2 className="mb-4 text-3xl font-bold">开始用 AI 赚钱</h2>
        <div className="flex justify-center gap-4">
          <Link href="/generate">
            <Button size="lg">
              免费开始
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          <Link href="/pricing">
            <Button variant="outline" size="lg">
              查看定价
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}
