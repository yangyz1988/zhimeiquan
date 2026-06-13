"use client";

import { useState } from "react";
import { Zap, BarChart3, Lightbulb, Sparkles, Send } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/toaster";

/* ------------------------------------------------------------------ */
/*  Data                                                               */
/* ------------------------------------------------------------------ */

const experts = [
  { id: "copywriting", label: "爆款文案专家", icon: <Zap className="h-4 w-4" /> },
  { id: "data", label: "数据分析专家", icon: <BarChart3 className="h-4 w-4" /> },
  { id: "creative", label: "创意策划专家", icon: <Lightbulb className="h-4 w-4" /> },
];

const coreEngines = [
  { title: "爆款生成", icon: "⚡", desc: "AI一键生成爆款标题" },
  { title: "对标拆解", icon: "📊", desc: "拆解爆款背后的逻辑" },
  { title: "自动改写", icon: "🔄", desc: "智能改写避免重复" },
  { title: "Fire Score", icon: "🔥", desc: "五维度综合评分" },
];

const platformExperts = [
  { title: "抖音", icon: "🎵", desc: "短视频爆款策略" },
  { title: "小红书", icon: "📕", desc: "种草笔记创作" },
  { title: "B站", icon: "📺", desc: "长视频内容策划" },
  { title: "公众号", icon: "💬", desc: "图文深度内容" },
];

const otherExperts = [
  { title: "文案专家", icon: "✍️", desc: "标题+开头+结构" },
  { title: "视觉专家", icon: "🎨", desc: "封面+配图+排版" },
  { title: "运营专家", icon: "📈", desc: "冷启动+增长" },
  { title: "变现专家", icon: "💰", desc: "商业化路径设计" },
];

/* ------------------------------------------------------------------ */
/*  Sub-components                                                     */
/* ------------------------------------------------------------------ */

function ExpertCard({
  title,
  icon,
  desc,
  glowClass,
}: {
  title: string;
  icon: string;
  desc: string;
  glowClass: string;
}) {
  return (
    <div
      className={`glass-card relative overflow-hidden group transition-all duration-300 hover:-translate-y-1 hover:shadow-xl ${glowClass}`}
    >
      <div className="p-5 space-y-2">
        <div
          className={`text-4xl drop-shadow-lg transition-transform duration-300 group-hover:scale-110`}
        >
          {icon}
        </div>
        <CardTitle className="text-sm font-semibold">{title}</CardTitle>
        <CardDescription className="text-xs">{desc}</CardDescription>
      </div>
    </div>
  );
}

function SectionHeading({
  title,
  gradientClass,
}: {
  title: string;
  gradientClass: string;
}) {
  return (
    <h2 className="text-xl font-semibold">
      <span className={gradientClass}>{title}</span>
      <span className="inline-block h-[2px] w-10 -translate-y-[2px] ml-2 bg-gradient-to-r from-orange-500 to-pink-500 rounded-full" />
    </h2>
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function ExpertsPage() {
  const [selectedExpert, setSelectedExpert] = useState("copywriting");
  const [question, setQuestion] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = () => {
    if (!question.trim()) {
      toast("请输入你的问题", "error");
      return;
    }
    setSubmitting(true);
    const expertName = experts.find((e) => e.id === selectedExpert)?.label ?? "";
    setTimeout(() => {
      toast(`${expertName}正在分析你的问题，请稍候...`, "success");
      setSubmitting(false);
      setQuestion("");
    }, 1200);
  };

  return (
    <div className="relative min-h-screen bg-grid">
      {/* Decorative glow orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-32 -left-32 h-[500px] w-[500px] rounded-full bg-purple-500/10 blur-[120px]" />
        <div className="absolute top-1/2 right-0 h-[400px] w-[400px] rounded-full bg-blue-500/10 blur-[120px]" />
        <div className="absolute -bottom-32 left-1/3 h-[350px] w-[350px] rounded-full bg-orange-500/10 blur-[100px]" />
      </div>

      <div className="relative container py-10 space-y-10 max-w-5xl mx-auto">
        {/* ---------- Header ---------- */}
        <div className="text-center space-y-4">
          <Badge
            variant="secondary"
            className="px-4 py-1.5 text-sm glass-card border-orange-500/30"
          >
            <Sparkles className="h-3.5 w-3.5 mr-1.5 text-orange-400 inline" />
            50+领域专家AI加持
          </Badge>
          <h1 className="text-4xl md:text-5xl font-extrabold text-gradient tracking-tight">
            专家引擎
          </h1>
          <p className="text-muted-foreground max-w-xl mx-auto leading-relaxed">
            选择一位专家，输入你的问题，获取定制化爆款方案
          </p>
        </div>

        {/* ---------- Expert Selector ---------- */}
        <div className="flex flex-wrap items-center gap-3 justify-center">
          {experts.map((expert) => (
            <button
              key={expert.id}
              type="button"
              onClick={() => setSelectedExpert(expert.id)}
              className={`glass-card px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-300 cursor-pointer flex items-center gap-2 ${
                selectedExpert === expert.id
                  ? "border-orange-400/50 shadow-[0_0_20px_rgba(249,115,22,0.25)] scale-[1.03]"
                  : "border-white/10 hover:border-white/20 opacity-70 hover:opacity-100"
              }`}
            >
              {expert.icon}
              <span>{expert.label}</span>
            </button>
          ))}
        </div>

        {/* ---------- Consultation ---------- */}
        <Card className="glass-card border-white/10">
          <CardHeader>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Send className="h-4 w-4 text-orange-400" />
              专家咨询
            </CardTitle>
            <CardDescription>
              当前选中：
              <span className="text-orange-400 font-medium">
                {experts.find((e) => e.id === selectedExpert)?.label}
              </span>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="例如：如何用信息差方法做AI副业选题？"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={4}
              className="glass-card border-white/10 focus:border-orange-400/50 bg-white/[0.03]"
            />
            <Button
              onClick={handleSubmit}
              disabled={submitting}
              className="bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600 text-white font-medium shadow-lg shadow-orange-500/20 transition-all duration-300 hover:shadow-orange-500/40 hover:-translate-y-0.5"
            >
              {submitting ? (
                <>
                  <span className="animate-pulse mr-2">分析中...</span>
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  咨询专家
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* ---------- Core Engines ---------- */}
        <div className="space-y-4">
          <SectionHeading title="核心引擎" gradientClass="text-gradient" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {coreEngines.map((item) => (
              <ExpertCard key={item.title} {...item} glowClass="glow-orange" />
            ))}
          </div>
        </div>

        {/* ---------- Platform Experts ---------- */}
        <div className="space-y-4">
          <SectionHeading title="平台专家" gradientClass="text-blue-400" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {platformExperts.map((item) => (
              <ExpertCard key={item.title} {...item} glowClass="glow-blue" />
            ))}
          </div>
        </div>

        {/* ---------- Other Experts ---------- */}
        <div className="space-y-4">
          <SectionHeading title="创作/运营/数据专家" gradientClass="text-purple-400" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {otherExperts.map((item) => (
              <ExpertCard key={item.title} {...item} glowClass="glow-purple" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
