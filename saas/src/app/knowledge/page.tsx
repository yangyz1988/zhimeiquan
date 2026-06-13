"use client";

import Link from "next/link";
import {
  Crown,
  Eye,
  MessageSquare,
  Shield,
  Type,
  Cpu,
  BookOpen,
  PenTool,
  Target,
  ArrowRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

/* ------------------------------------------------------------------ */
/*  Data                                                               */
/* ------------------------------------------------------------------ */

const layers = [
  {
    level: "L9",
    title: "专家智能体",
    desc: "50+专家 4层级协作",
    color: "purple",
    glowClass: "glow-purple",
    icon: Crown,
    badgeBg: "dark:bg-purple-950/60 dark:text-purple-300 bg-purple-100 text-purple-700",
  },
  {
    level: "L8",
    title: "视觉音频优化",
    desc: "封面+配图+口播节奏",
    color: "purple-600",
    glowClass: "glow-purple",
    icon: Eye,
    badgeBg: "dark:bg-purple-950/60 dark:text-purple-300 bg-purple-100 text-purple-700",
  },
  {
    level: "L7",
    title: "运营SOP体系",
    desc: "评论区+冷启动+数据回流",
    color: "indigo-500",
    glowClass: "glow-blue",
    icon: MessageSquare,
    badgeBg: "dark:bg-indigo-950/60 dark:text-indigo-300 bg-indigo-100 text-indigo-700",
  },
  {
    level: "L6",
    title: "爆款概率保障",
    desc: "概率提升至95%+",
    color: "blue",
    glowClass: "glow-blue",
    icon: Shield,
    badgeBg: "dark:bg-blue-950/60 dark:text-blue-300 bg-blue-100 text-blue-700",
  },
  {
    level: "L5",
    title: "标题类型库",
    desc: "13种爆款标题类型",
    color: "sky-500",
    glowClass: "",
    icon: Type,
    badgeBg: "dark:bg-sky-950/60 dark:text-sky-300 bg-sky-100 text-sky-700",
  },
  {
    level: "L4",
    title: "平台算法适配",
    desc: "13个平台核心指标",
    color: "teal-500",
    glowClass: "",
    icon: Cpu,
    badgeBg: "dark:bg-teal-950/60 dark:text-teal-300 bg-teal-100 text-teal-700",
  },
  {
    level: "L3",
    title: "六大方法论",
    desc: "反常识+人性+数字...",
    color: "green",
    glowClass: "",
    icon: BookOpen,
    badgeBg: "dark:bg-green-950/60 dark:text-green-300 bg-green-100 text-green-700",
  },
  {
    level: "L2",
    title: "四步创作法",
    desc: "选题→开头→正文→结尾",
    color: "lime-500",
    glowClass: "",
    icon: PenTool,
    badgeBg: "dark:bg-lime-950/60 dark:text-lime-300 bg-lime-100 text-lime-700",
  },
  {
    level: "L1",
    title: "爆款底层逻辑",
    desc: "CTR核心公式",
    color: "amber",
    glowClass: "",
    icon: Target,
    badgeBg: "dark:bg-amber-950/60 dark:text-amber-300 bg-amber-100 text-amber-700",
  },
];

const quickLinks = [
  {
    title: "内容生成",
    desc: "开始创作爆款内容",
    href: "/generate",
    glowClass: "glow-orange",
    icon: PenTool,
    iconColor: "text-orange-400",
  },
  {
    title: "专家引擎",
    desc: "获取专家定制方案",
    href: "/experts",
    glowClass: "glow-purple",
    icon: Cpu,
    iconColor: "text-purple-400",
  },
  {
    title: "运营中心",
    desc: "冷启动+运营SOP",
    href: "/operations",
    glowClass: "glow-green",
    icon: MessageSquare,
    iconColor: "text-green-400",
  },
];

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function KnowledgePage() {
  return (
    <div className="relative min-h-screen">
      {/* ---- Background grid ---- */}
      <div className="bg-grid pointer-events-none fixed inset-0 z-0" />

      {/* ---- Main content ---- */}
      <div className="relative z-10">
        {/* Gradient glows at edges */}
        <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
          <div className="absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full bg-orange-500/10 blur-[120px]" />
          <div className="absolute -top-20 -right-20 w-[400px] h-[400px] rounded-full bg-blue-500/10 blur-[120px]" />
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full bg-purple-500/8 blur-[120px]" />
        </div>

        <div className="max-w-3xl mx-auto px-4 py-12 sm:py-16">
          {/* ---- Hero section ---- */}
          <div className="text-center mb-14">
            <Badge
              variant="secondary"
              className="mb-4 dark:bg-white/10 dark:text-gray-200 border-white/20"
            >
              从0到爆款的完整知识金字塔
            </Badge>
            <h1 className="text-gradient text-4xl sm:text-5xl font-extrabold tracking-tight mb-4">
              九层知识体系
            </h1>
            <p className="text-muted-foreground text-lg max-w-xl mx-auto">
              系统化构建爆款能力，底层逻辑 → 顶层运营
            </p>
          </div>

          {/* ---- Vertical timeline ---- */}
          <div className="relative flex gap-5">
            {/* Connecting line */}
            <div className="flex-shrink-0 w-[3px] rounded-full bg-gradient-to-b from-purple-500 via-blue-500 to-amber-500 absolute left-[27px] top-0 bottom-0 opacity-30" />

            {layers.map((layer, idx) => {
              const Icon = layer.icon;
              return (
                <div
                  key={layer.level}
                  className="relative flex-1 pt-3 first:pt-0"
                  style={{ marginTop: idx === 0 ? 0 : -8 }}
                >
                  {/* Timeline dot */}
                  <div className="absolute left-[20px] top-[14px] z-10 flex items-center justify-center">
                    <div
                      className={`w-5 h-5 rounded-full border-2 dark:bg-gray-950 ${
                        idx < 4
                          ? "bg-white border-purple-400 shadow-[0_0_10px_rgba(168,85,247,.4)]"
                          : "bg-white border-gray-300 dark:border-gray-600"
                      }`}
                    />
                  </div>

                  {/* Card */}
                  <div
                    className={`
                      glass-card group rounded-xl p-4
                      border-l-4 border-l-${layer.color}
                      transition-all duration-300
                      hover:scale-[1.015] hover:-translate-y-0.5
                      ${layer.glowClass ? `${layer.glowClass} rounded-t-xl rounded-b-none` : ""}
                    `}
                  >
                    <div className="flex items-center gap-4">
                      {/* Icon circle */}
                      <div
                        className={`
                          flex-shrink-0 w-11 h-11 rounded-full
                          flex items-center justify-center
                          dark:bg-white/5 ring-1 dark:ring-white/10
                          group-hover:dark:ring-white/20 transition
                        `}
                      >
                        <Icon className="w-5 h-5 dark:text-white/70 group-hover:text-white transition-colors" />
                      </div>

                      {/* Level badge */}
                      <div
                        className={`
                          flex-shrink-0 w-11 h-11 rounded-full
                          flex items-center justify-center text-xs font-bold
                          dark:bg-white/5 dark:text-white/60
                          group-hover:bg-white/10 transition
                        `}
                      >
                        {layer.level}
                      </div>

                      {/* Text */}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-base font-semibold dark:text-white/90 group-hover:text-white transition">
                          {layer.title}
                        </h3>
                        <p className="text-sm text-muted-foreground">
                          {layer.desc}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* ---- Quick links ---- */}
          <div className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-4">
            {quickLinks.map((link) => {
              const Icon = link.icon;
              return (
                <Link key={link.href} href={link.href} passHref>
                  <div
                    className={`
                      glass-card rounded-xl p-5
                      ${link.glowClass} rounded-t-xl rounded-b-none
                      group cursor-pointer
                      transition-all duration-300
                      hover:scale-[1.03] hover:-translate-y-1
                    `}
                  >
                    <div className="flex flex-col items-center text-center gap-3">
                      <div
                        className={`
                          w-12 h-12 rounded-full
                          dark:bg-white/5 flex items-center justify-center
                          ${link.iconColor}
                          group-hover:dark:bg-white/10 transition
                        `}
                      >
                        <Icon className="w-6 h-6" />
                      </div>
                      <div>
                        <div className="font-semibold dark:text-white/90 group-hover:text-white transition text-base">
                          {link.title}
                        </div>
                        <div className="text-sm text-muted-foreground mt-1">
                          {link.desc}
                        </div>
                      </div>
                      <div className="mt-auto w-full">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="w-full dark:text-white/50 dark:hover:text-white/90 dark:hover:bg-white/10"
                        >
                          进入
                          <ArrowRight className="ml-2 w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
