"use client";

import { useState } from "react";
import { Zap, BarChart3, Lightbulb } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/toaster";

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

function ExpertCard({ title, icon, desc }: { title: string; icon: string; desc: string }) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="py-3">
        <div className="text-xl mb-1">{icon}</div>
        <CardTitle className="text-sm">{title}</CardTitle>
        <CardDescription className="text-xs">{desc}</CardDescription>
      </CardHeader>
    </Card>
  );
}

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
    <div className="container py-8 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <Badge variant="secondary">50+领域专家AI加持</Badge>
        <h1 className="text-3xl font-bold">专家引擎</h1>
        <p className="text-muted-foreground">
          选择一位专家，输入你的问题，获取定制化爆款方案
        </p>
      </div>

      {/* Expert Selector */}
      <div className="flex flex-wrap items-center gap-2 justify-center">
        {experts.map((expert) => (
          <Badge
            key={expert.id}
            variant={selectedExpert === expert.id ? "default" : "outline"}
            className="cursor-pointer px-4 py-1.5 text-sm hover:opacity-80 transition-opacity"
            onClick={() => setSelectedExpert(expert.id)}
          >
            {expert.icon}
            <span className="ml-1">{expert.label}</span>
          </Badge>
        ))}
      </div>

      {/* Consultation */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">专家咨询</CardTitle>
          <CardDescription>
            当前选中：{experts.find((e) => e.id === selectedExpert)?.label}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            placeholder="例如：如何用信息差方法做AI副业选题？"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={4}
          />
          <Button
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? "分析中..." : "咨询专家"}
          </Button>
        </CardContent>
      </Card>

      {/* Core Engines */}
      <div className="space-y-2">
        <h2 className="text-lg font-semibold">核心引擎</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {coreEngines.map((item) => (
            <ExpertCard key={item.title} {...item} />
          ))}
        </div>
      </div>

      {/* Platform Experts */}
      <div className="space-y-2">
        <h2 className="text-lg font-semibold">平台专家</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {platformExperts.map((item) => (
            <ExpertCard key={item.title} {...item} />
          ))}
        </div>
      </div>

      {/* Other Experts */}
      <div className="space-y-2">
        <h2 className="text-lg font-semibold">创作/运营/数据专家</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {otherExperts.map((item) => (
            <ExpertCard key={item.title} {...item} />
          ))}
        </div>
      </div>
    </div>
  );
}
