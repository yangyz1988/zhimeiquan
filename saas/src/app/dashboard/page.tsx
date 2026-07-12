"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DashboardContent } from "@/components/dashboard-content";
import {
  Sparkles, BarChart3, Activity, FileText, TrendingUp,
  Clock, ArrowRight, Loader2, AlertCircle, Plus, Eye,
} from "lucide-react";
import { toast } from "@/components/toaster";

interface RecentOutput {
  id: string;
  title: string;
  platform: string;
  createdAt: string;
  fireScore: string | null;
}

interface UserStats {
  projectCount: number;
  generationCount: number;
  avgFireScore: number | null;
  recentOutputs: RecentOutput[];
}

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState(false);

  useEffect(() => {
    fetchUserStats();
  }, []);

  const fetchUserStats = async () => {
    setStatsLoading(true);
    setStatsError(false);
    try {
      const res = await fetch("/api/projects");
      if (!res.ok) throw new Error("Failed to load");
      const projects = await res.json();

      const projectCount = Array.isArray(projects) ? projects.length : 0;
      const allOutputs: RecentOutput[] = [];
      let totalFireScore = 0;
      let scoredCount = 0;

      if (Array.isArray(projects)) {
        projects.forEach((p: Record<string, unknown>) => {
          const outputs = Array.isArray((p as { outputs?: unknown[] }).outputs)
            ? (p as { outputs: Array<Record<string, unknown>> }).outputs
            : [];
          outputs.forEach((o: Record<string, unknown>) => {
            allOutputs.push({
              id: (o as { id: string }).id || "",
              title: (o as { title?: string }).title || (p as { name: string }).name || "未命名",
              platform: (p as { platform: string }).platform || "未知",
              createdAt: (o as { createdAt?: string }).createdAt || (p as { createdAt: string }).createdAt || "",
              fireScore: (o as { fireScore: string | null }).fireScore ?? null,
            });
            if (o.fireScore) {
              try {
                const s = typeof o.fireScore === "string" ? JSON.parse(o.fireScore) : o.fireScore;
                const score = (s as Record<string, number>).total || s;
                if (typeof score === "number") {
                  totalFireScore += score;
                  scoredCount++;
                }
              } catch { /* skip */ }
            }
          });
        });
      }

      const generationCount = allOutputs.length;
      const avgFireScore = scoredCount > 0 ? Math.round(totalFireScore / scoredCount) : null;

      const sortedOutputs = allOutputs
        .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
        .slice(0, 5);

      setStats({ projectCount, generationCount, avgFireScore, recentOutputs: sortedOutputs });
    } catch (error) {
      console.error(error);
      setStatsError(true);
      toast("加载统计数据失败", "error");
    } finally {
      setStatsLoading(false);
    }
  };

  const parseFireScore = (score: string | null): number | null => {
    if (!score) return null;
    try {
      const s = JSON.parse(score);
      return s.total ?? s;
    } catch {
      return null;
    }
  };

  const fireScoreColor = (score: number): string => {
    if (score >= 90) return "text-green-400";
    if (score >= 80) return "text-yellow-400";
    if (score >= 70) return "text-orange-400";
    return "text-red-400";
  };

  const quickActions = [
    {
      label: "新建项目",
      desc: "创建新的内容生成项目",
      icon: Plus,
      href: "/generate",
      gradient: "from-orange-500/20 to-pink-500/20 border-orange-500/20",
      iconBg: "bg-orange-500/20 text-orange-400",
    },
    {
      label: "查看分析",
      desc: "深入分析内容表现数据",
      icon: BarChart3,
      href: "/analytics",
      gradient: "from-blue-500/20 to-cyan-500/20 border-blue-500/20",
      iconBg: "bg-blue-500/20 text-blue-400",
    },
    {
      label: "竞品监控",
      desc: "追踪竞品内容策略趋势",
      icon: Activity,
      href: "/insights",
      gradient: "from-purple-500/20 to-pink-500/20 border-purple-500/20",
      iconBg: "bg-purple-500/20 text-purple-400",
    },
  ];

  const platformColor = (platform: string): string => {
    const map: Record<string, string> = {
      "抖音": "bg-red-500/20 text-red-400",
      "小红书": "bg-pink-500/20 text-pink-400",
      "B站": "bg-blue-500/20 text-blue-400",
      "公众号": "bg-green-500/20 text-green-400",
      "YouTube": "bg-red-600/20 text-red-500",
      "TikTok": "bg-cyan-500/20 text-cyan-400",
      "快手": "bg-purple-500/20 text-purple-400",
      "微博": "bg-amber-500/20 text-amber-400",
      "知乎": "bg-indigo-500/20 text-indigo-400",
      "头条": "bg-rose-500/20 text-rose-400",
    };
    return map[platform] || "bg-gray-500/20 text-gray-400";
  };

  const formatTime = (dateStr: string): string => {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 60) return `${diffMin}分钟前`;
    const diffHour = Math.floor(diffMin / 60);
    if (diffHour < 24) return `${diffHour}小时前`;
    const diffDay = Math.floor(diffHour / 24);
    if (diffDay < 7) return `${diffDay}天前`;
    return d.toLocaleDateString("zh-CN");
  };

  return (
    <div className="container py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-orange-500/20 bg-gradient-to-r from-orange-500/10 via-orange-500/5 to-transparent p-6 md:p-8">
        <div className="relative z-10 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-2">
            <h1 className="flex items-center gap-2 text-3xl font-bold">
              <Sparkles className="h-8 w-8 text-orange-400" />
              欢迎回到智媒圈
            </h1>
            <p className="text-white/50 max-w-lg">
              一站式自媒体内容创作与数据分析平台。管理你的项目，追踪内容表现，用 AI 驱动你的创作。
            </p>
          </div>

          {/* Stats Summary */}
          {statsLoading ? (
            <div className="flex items-center gap-4 rounded-xl border border-white/10 bg-black/20 p-4 backdrop-blur">
              <Loader2 className="h-5 w-5 animate-spin text-orange-400" />
              <span className="text-sm text-white/40">加载中...</span>
            </div>
          ) : statsError ? (
            <div className="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/5 p-4 backdrop-blur">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <span className="text-sm text-red-400">加载失败</span>
              <Button variant="ghost" size="sm" onClick={fetchUserStats} className="text-white/60">
                重试
              </Button>
            </div>
          ) : stats ? (
            <div className="flex flex-wrap gap-4">
              <div className="rounded-xl border border-white/10 bg-black/20 px-5 py-3 text-center backdrop-blur">
                <div className="text-2xl font-bold text-orange-400">{stats.projectCount}</div>
                <div className="text-xs text-white/40">项目数</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/20 px-5 py-3 text-center backdrop-blur">
                <div className="text-2xl font-bold text-blue-400">{stats.generationCount}</div>
                <div className="text-xs text-white/40">生成次数</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/20 px-5 py-3 text-center backdrop-blur">
                <div className={`text-2xl font-bold ${stats.avgFireScore ? "text-orange-400" : "text-white/30"}`}>
                  {stats.avgFireScore ?? "--"}
                </div>
                <div className="text-xs text-white/40">平均 Fire Score</div>
              </div>
            </div>
          ) : null}
        </div>
        {/* Decorative background element */}
        <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-orange-500/[0.08] blur-[80px]" />
      </div>

      {/* Quick Action Cards */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-white/70">快捷操作</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {quickActions.map((action) => (
            <Card
              key={action.label}
              className={`cursor-pointer border bg-gradient-to-br ${action.gradient} transition-all hover:scale-[1.02] hover:shadow-lg`}
              onClick={() => router.push(action.href)}
            >
              <CardContent className="flex items-center gap-4 p-5">
                <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${action.iconBg}`}>
                  <action.icon className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-white/80">{action.label}</h3>
                  <p className="text-xs text-white/40">{action.desc}</p>
                </div>
                <ArrowRight className="h-4 w-4 text-white/20" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Recent Outputs */}
      {stats && stats.recentOutputs.length > 0 && (
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white/70">最近生成</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/generate")}
              className="text-white/50 hover:text-orange-400"
            >
              查看全部
              <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Button>
          </div>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {stats.recentOutputs.map((output) => {
              const score = parseFireScore(output.fireScore);
              return (
                <Card
                  key={output.id}
                  className="cursor-pointer border-white/5 bg-white/[0.02] transition-all hover:border-orange-500/20 hover:bg-white/[0.04]"
                  onClick={() => router.push("/generate")}
                >
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 shrink-0 text-white/30" />
                        <span className="truncate text-sm font-medium text-white/70">{output.title}</span>
                      </div>
                      <div className="mt-1.5 flex items-center gap-2">
                        <Badge className={`text-[10px] ${platformColor(output.platform)}`} variant="outline">
                          {output.platform}
                        </Badge>
                        <span className="flex items-center gap-1 text-xs text-white/30">
                          <Clock className="h-3 w-3" />
                          {formatTime(output.createdAt)}
                        </span>
                      </div>
                    </div>
                    {score !== null && (
                      <div className={`ml-3 text-right`}>
                        <div className={`text-lg font-bold ${fireScoreColor(score)}`}>{score}</div>
                        <div className="text-[10px] text-white/30">Fire</div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Existing Dashboard Content (project list) */}
      <DashboardContent />
    </div>
  );
}
