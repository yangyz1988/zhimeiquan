"use client";

import { useState, useEffect, useCallback } from "react";
import { ABTestDashboard } from "@/components/ab-test-dashboard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  FlaskConical, TrendingUp, Clock, AlertCircle, Loader2,
  CheckCircle2, Play, Pause, ArrowRight, Sparkles,
  Lightbulb, ListChecks, Target, Zap, FileText,
} from "lucide-react";
import { toast } from "@/components/toaster";

interface TestSummary {
  total: number;
  running: number;
  completed: number;
  draft: number;
  paused: number;
  hasWinner: number;
  avgConfidence: number | null;
}

interface ActiveTestInfo {
  test_id: string;
  name: string;
  status: string;
  variants: { id: string; title: string }[];
  platforms: string[];
  created_at: string;
  duration_days: number;
  winner: string | null;
  confidence: number | null;
}

export default function ABTestPage() {
  const [testSummary, setTestSummary] = useState<TestSummary | null>(null);
  const [activeTests, setActiveTests] = useState<ActiveTestInfo[]>([]);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState(false);
  const [showQuickStart, setShowQuickStart] = useState(true);

  const fetchTestSummary = useCallback(async () => {
    setSummaryLoading(true);
    setSummaryError(false);
    try {
      const res = await fetch("/api/ab-test");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const allTests: ActiveTestInfo[] = data.tests || [];

      const summary: TestSummary = {
        total: allTests.length,
        running: allTests.filter((t) => t.status === "running").length,
        completed: allTests.filter((t) => t.status === "completed").length,
        draft: allTests.filter((t) => t.status === "draft").length,
        paused: allTests.filter((t) => t.status === "paused").length,
        hasWinner: allTests.filter((t) => t.winner).length,
        avgConfidence: null,
      };

      const withConfidence = allTests.filter((t) => t.confidence != null);
      if (withConfidence.length > 0) {
        summary.avgConfidence = Math.round(
          withConfidence.reduce((sum, t) => sum + (t.confidence || 0), 0) / withConfidence.length
        );
      }

      setTestSummary(summary);
      setActiveTests(allTests.filter((t) => t.status === "running" || t.status === "paused"));

      // Auto-hide quick start for returning users
      if (allTests.length > 0) {
        setShowQuickStart(false);
      }
    } catch (error) {
      console.error(error);
      setSummaryError(true);
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTestSummary();
  }, [fetchTestSummary]);

  const formatDate = (dateStr: string): string => {
    try {
      return new Date(dateStr).toLocaleDateString("zh-CN", {
        month: "2-digit", day: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  const getDaysRemaining = (test: ActiveTestInfo): string => {
    if (!test.duration_days || !test.created_at) return "--";
    const created = new Date(test.created_at).getTime();
    const elapsed = (Date.now() - created) / (1000 * 60 * 60 * 24);
    const remaining = Math.max(0, test.duration_days - elapsed);
    return Math.ceil(remaining) + "天";
  };

  const statusColor = (status: string): string => {
    switch (status) {
      case "running": return "text-green-400 bg-green-500/10";
      case "paused": return "text-amber-400 bg-amber-500/10";
      case "completed": return "text-blue-400 bg-blue-500/10";
      default: return "text-white/40 bg-white/5";
    }
  };

  const statusLabel = (status: string): string => {
    switch (status) {
      case "running": return "运行中";
      case "paused": return "已暂停";
      case "completed": return "已完成";
      case "draft": return "草稿";
      default: return status;
    }
  };

  return (
    <div className="container py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-3xl font-bold">
            <FlaskConical className="h-7 w-7 text-orange-400" />
            A/B 测试
          </h1>
          <p className="mt-1 text-muted-foreground">
            科学对比不同内容变体的表现，用数据驱动内容优化决策
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchTestSummary}
            disabled={summaryLoading}
            className="border-white/10 text-white/50"
          >
            <Loader2 className={`mr-1 h-3.5 w-3.5 ${summaryLoading ? "animate-spin" : "hidden"}`} />
            刷新
          </Button>
          <Button
            onClick={() => setShowQuickStart(!showQuickStart)}
            variant="ghost"
            size="sm"
            className="text-white/40 hover:text-white/70"
          >
            {showQuickStart ? "收起指南" : "显示指南"}
          </Button>
        </div>
      </div>

      {/* Active Tests Summary Banner */}
      {summaryLoading ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="glass-card h-16 animate-pulse rounded-xl border-white/5" />
          ))}
        </div>
      ) : summaryError ? (
        <Card className="border-red-500/20 bg-red-500/5">
          <CardContent className="flex items-center gap-3 py-4">
            <AlertCircle className="h-5 w-5 text-red-400 shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-white/60">测试摘要加载失败</p>
            </div>
            <Button variant="outline" size="sm" onClick={fetchTestSummary} className="border-white/10 shrink-0">
              重试
            </Button>
          </CardContent>
        </Card>
      ) : testSummary ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          <Card className="glass-card border-white/5 glow-blue">
            <CardContent className="flex flex-col items-center py-3 text-center">
              <span className="text-2xl font-bold text-white">{testSummary.total}</span>
              <span className="text-xs text-white/40">全部测试</span>
            </CardContent>
          </Card>
          <Card className="glass-card border-green-500/10 glow-green">
            <CardContent className="flex flex-col items-center py-3 text-center">
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-full bg-green-400 animate-pulse" />
                <span className="text-2xl font-bold text-green-400">{testSummary.running}</span>
              </div>
              <span className="text-xs text-white/40">运行中</span>
            </CardContent>
          </Card>
          <Card className="glass-card border-blue-500/10 glow-blue">
            <CardContent className="flex flex-col items-center py-3 text-center">
              <span className="text-2xl font-bold text-blue-400">{testSummary.completed}</span>
              <span className="text-xs text-white/40">已完成</span>
            </CardContent>
          </Card>
          <Card className="glass-card border-amber-500/10">
            <CardContent className="flex flex-col items-center py-3 text-center">
              <span className="text-2xl font-bold text-amber-400">{testSummary.draft + testSummary.paused}</span>
              <span className="text-xs text-white/40">草稿/暂停</span>
            </CardContent>
          </Card>
          <Card className="glass-card border-orange-500/10 glow-orange">
            <CardContent className="flex flex-col items-center py-3 text-center">
              <span className="text-2xl font-bold text-orange-400">{testSummary.hasWinner}</span>
              <span className="text-xs text-white/40">已有胜出</span>
            </CardContent>
          </Card>
        </div>
      ) : null}

      {/* Active Running Tests */}
      {activeTests.length > 0 && (
        <div>
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white/70">
            <Play className="h-4 w-4 text-green-400" />
            进行中的测试
            <Badge className="bg-green-500/10 text-green-400 border-green-500/20 text-xs">
              {activeTests.length}
            </Badge>
          </h2>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {activeTests.map((test) => (
              <Card
                key={test.test_id}
                className="border-green-500/10 bg-gradient-to-br from-green-500/5 to-transparent transition-all hover:border-green-500/20"
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="min-w-0 flex-1">
                      <h3 className="truncate font-medium text-white/70">{test.name || test.test_id}</h3>
                      <p className="text-xs text-white/30">{test.test_id}</p>
                    </div>
                    <Badge className={`shrink-0 ml-2 ${statusColor(test.status)}`}>
                      {statusLabel(test.status)}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-white/40">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDate(test.created_at)} · 剩余 {getDaysRemaining(test)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Target className="h-3 w-3" />
                      {test.platforms?.join("/") || "--"}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center gap-2 text-xs text-white/30">
                    <span>变体: {test.variants?.map((v) => v.title).join(" vs ") || "--"}</span>
                  </div>
                  {test.confidence != null && (
                    <div className="mt-2 flex items-center gap-1.5">
                      <div className="h-1 flex-1 rounded-full bg-white/5">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-green-500 to-emerald-400"
                          style={{ width: `${test.confidence}%` }}
                        />
                      </div>
                      <span className="text-xs text-green-400">{test.confidence}% 置信度</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Quick Start Guide */}
      {showQuickStart && (
        <Card className="overflow-hidden border-white/5 bg-gradient-to-br from-orange-500/[0.03] via-purple-500/[0.02] to-transparent">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-500/10">
                <Lightbulb className="h-4 w-4 text-orange-400" />
              </div>
              <div>
                <CardTitle className="text-base text-white/80">A/B 测试快速入门</CardTitle>
                <CardDescription>三个简单步骤，开始你的第一次内容对比测试</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              {/* Step 1 */}
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-orange-500 to-pink-500 text-xs font-bold text-white">
                    1
                  </span>
                  <span className="text-sm font-medium text-white/60">创建测试</span>
                </div>
                <div className="space-y-2 text-xs text-white/40">
                  <div className="flex items-start gap-2">
                    <FileText className="h-3.5 w-3.5 mt-0.5 shrink-0 text-orange-400/60" />
                    <span>准备两个内容变体（如不同标题或封面风格）</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <Target className="h-3.5 w-3.5 mt-0.5 shrink-0 text-orange-400/60" />
                    <span>选择目标平台和测试时长（建议 7-14 天）</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <Sparkles className="h-3.5 w-3.5 mt-0.5 shrink-0 text-orange-400/60" />
                    <span>点击"新建测试"并填写变体信息</span>
                  </div>
                </div>
              </div>

              {/* Step 2 */}
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 text-xs font-bold text-white">
                    2
                  </span>
                  <span className="text-sm font-medium text-white/60">收集数据</span>
                </div>
                <div className="space-y-2 text-xs text-white/40">
                  <div className="flex items-start gap-2">
                    <Play className="h-3.5 w-3.5 mt-0.5 shrink-0 text-blue-400/60" />
                    <span>启动测试后，系统将自动跟踪各变体的表现数据</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <Clock className="h-3.5 w-3.5 mt-0.5 shrink-0 text-blue-400/60" />
                    <span>测试运行期间实时监控曝光、互动率等核心指标</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <Zap className="h-3.5 w-3.5 mt-0.5 shrink-0 text-blue-400/60" />
                    <span>可在测试过程中随时暂停或调整</span>
                  </div>
                </div>
              </div>

              {/* Step 3 */}
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-green-500 to-emerald-500 text-xs font-bold text-white">
                    3
                  </span>
                  <span className="text-sm font-medium text-white/60">分析结果</span>
                </div>
                <div className="space-y-2 text-xs text-white/40">
                  <div className="flex items-start gap-2">
                    <TrendingUp className="h-3.5 w-3.5 mt-0.5 shrink-0 text-green-400/60" />
                    <span>测试结束后，系统自动生成对比报告</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0 text-green-400/60" />
                    <span>查看哪个变体表现更优，获得数据驱动的决策依据</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <ListChecks className="h-3.5 w-3.5 mt-0.5 shrink-0 text-green-400/60" />
                    <span>将胜出版本应用到实际内容策略中</span>
                  </div>
                </div>
              </div>
            </div>

            {testSummary && testSummary.total === 0 && (
              <div className="mt-4 flex justify-center">
                <Button
                  onClick={() => {
                    // Trigger the create modal in the existing dashboard
                    const createBtn = document.querySelector('[class*="bg-gradient-to-r from-orange-500 to-pink-500"]') as HTMLButtonElement;
                    if (createBtn && createBtn.textContent?.includes("新建测试")) {
                      createBtn.click();
                    }
                  }}
                  className="bg-gradient-to-r from-orange-500 to-pink-500 text-white shadow-lg hover:from-orange-600 hover:to-pink-600"
                >
                  <FlaskConical className="mr-1.5 h-4 w-4" />
                  创建第一个测试
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Performance Insight Tip */}
      {testSummary && testSummary.completed > 0 && testSummary.hasWinner === 0 && (
        <Card className="border-amber-500/20 bg-amber-500/5">
          <CardContent className="flex items-center gap-3 py-4">
            <AlertCircle className="h-5 w-5 text-amber-400 shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-white/60">
                你有 {testSummary.completed} 个已完成的测试尚未确定胜出者。检查测试详情，标记表现更优的变体。
              </p>
            </div>
            <ArrowRight className="h-4 w-4 text-amber-400 shrink-0" />
          </CardContent>
        </Card>
      )}

      {/* Existing AB Test Dashboard */}
      <ABTestDashboard />
    </div>
  );
}
