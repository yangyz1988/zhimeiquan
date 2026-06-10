"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const layers = [
  {
    level: "L9",
    title: "专家智能体",
    desc: "50+专家 4层级协作",
    color: "border-l-purple-500",
    badgeColor: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
  },
  {
    level: "L8",
    title: "视觉音频优化",
    desc: "封面+配图+口播节奏",
    color: "border-l-purple-600",
    badgeColor: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
  },
  {
    level: "L7",
    title: "运营SOP体系",
    desc: "评论区+冷启动+数据回流",
    color: "border-l-indigo-500",
    badgeColor: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300",
  },
  {
    level: "L6",
    title: "爆款概率保障",
    desc: "概率提升至95%+",
    color: "border-l-blue-500",
    badgeColor: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  },
  {
    level: "L5",
    title: "标题类型库",
    desc: "13种爆款标题类型",
    color: "border-l-sky-500",
    badgeColor: "bg-sky-100 text-sky-700 dark:bg-sky-900 dark:text-sky-300",
  },
  {
    level: "L4",
    title: "平台算法适配",
    desc: "13个平台核心指标",
    color: "border-l-teal-500",
    badgeColor: "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300",
  },
  {
    level: "L3",
    title: "六大方法论",
    desc: "反常识+人性+数字...",
    color: "border-l-green-500",
    badgeColor: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  },
  {
    level: "L2",
    title: "四步创作法",
    desc: "选题→开头→正文→结尾",
    color: "border-l-lime-500",
    badgeColor: "bg-lime-100 text-lime-700 dark:bg-lime-900 dark:text-lime-300",
  },
  {
    level: "L1",
    title: "爆款底层逻辑",
    desc: "CTR核心公式",
    color: "border-l-amber-500",
    badgeColor: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
  },
];

const quickLinks = [
  { title: "内容生成", desc: "开始创作爆款内容", href: "/generate", icon: "🚀" },
  { title: "专家引擎", desc: "获取专家定制方案", href: "/experts", icon: "🧠" },
  { title: "运营中心", desc: "冷启动+运营SOP", href: "/operations", icon: "📈" },
];

export default function KnowledgePage() {
  return (
    <div className="container py-8 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <Badge variant="secondary">从0到爆款的完整知识金字塔</Badge>
        <h1 className="text-3xl font-bold">九层知识体系</h1>
        <p className="text-muted-foreground">
          系统化构建爆款能力，底层逻辑→顶层运营
        </p>
      </div>

      {/* Knowledge Layers */}
      <div className="space-y-3">
        {layers.map((layer) => (
          <Card
            key={layer.level}
            className={`border-l-4 ${layer.color}`}
          >
            <CardHeader className="py-3 px-4">
              <div className="flex items-center gap-3">
                <Badge className={layer.badgeColor}>{layer.level}</Badge>
                <CardTitle className="text-base">{layer.title}</CardTitle>
                <CardDescription className="ml-auto text-sm">
                  {layer.desc}
                </CardDescription>
              </div>
            </CardHeader>
          </Card>
        ))}
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {quickLinks.map((link) => (
          <Link key={link.href} href={link.href}>
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
              <CardHeader>
                <div className="text-2xl mb-1">{link.icon}</div>
                <CardTitle className="text-base flex items-center gap-2">
                  {link.title}
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </CardTitle>
                <CardDescription>{link.desc}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
