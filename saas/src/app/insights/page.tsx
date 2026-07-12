"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { InsightsDashboard } from "@/components/insights-dashboard";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  TrendingUp, TrendingDown, Minus, Zap, Clock, Target,
  Sparkles, Loader2, AlertCircle, RefreshCw, Activity,
  Flame, BarChart3, Globe, ArrowUpRight, ArrowDownRight,
} from "lucide-react";
import { toast } from "@/components/toaster";

const PLATFORMS = [
  "抖音", "小红书", "B站", "公众号", "YouTube", "TikTok",
  "快手", "微博", "知乎", "头条",
];

const REFRESH_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

interface InsightSummary {
  totalTrends: number;
  risingCount: number;
  decliningCount: number;
  topPrediction: { topic: string; viralScore: number } | null;
  bestTimeSlot: { time: string; score: number } | null;
}

type SeverityLevel = "high" | "medium" | "low";

interface TrendItem {
  type: string;
  name: string;
  count: number;
  direction: string;
}

interface PredictionItem {
  topic: string;
  viral_score: number;
  reason: string;
  suggested_hook: string;
}

interface TimeSlotItem {
  time: string;
  score: number;
  reason: string;
}

export default function InsightsPage() {
  const [platform, setPlatform] = useState("抖音");
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summary, setSummary] = useState<InsightSummary | null>(null);
  const [summaryError, setSummaryError] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchInsightSummary = useCallback(async () => {
    setSummaryLoading(true);
    setSummaryError(false);
    try {
      const encoded = encodeURIComponent(platform);
      const [trendsRes, predictRes, timeRes] = await Promise.all([
        fetch(`/api/insights/trends/${encoded}`),
        fetch(`/api/insights/predict/${encoded}`),
        fetch(`/api/insights/posting-time/${encoded}`),
      ]);

      const trendsData = trendsRes.ok ? await trendsRes.json() : { trends: [] };
      const predictData = predictRes.ok ? await predictRes.json() : { predictions: [] };
      const timeData = timeRes.ok ? await timeRes.json() : { time_slots: [] };

      const trends: TrendItem[] = trendsData.trends || [];
      const predictions: PredictionItem[] = predictData.predictions || [];
      const timeSlots: TimeSlotItem[] = timeData.time_slots || [];

      const totalTrends = trends.length;
      const risingCount = trends.filter((t) => t.direction === "rising").length;
      const decliningCount = trends.filter((t) => t.direction === "declining").length;

      const topPrediction = predictions.length > 0
        ? predictions.reduce((best, p) => p.viral_score > best.viral_score ? p : best, predictions[0])
        : null;

      const bestTimeSlot = timeSlots.length > 0
        ? timeSlots.reduce((best, t) => t.score > best.score ? t : best, timeSlots[0])
        : null;

      setSummary({
        totalTrends,
        risingCount,
        decliningCount,
        topPrediction: topPrediction ? { topic: topPrediction.topic, viralScore: topPrediction.viral_score } : null,
        bestTimeSlot: bestTimeSlot ? { time: bestTimeSlot.time, score: bestTimeSlot.score } : null,
      });
      setLastRefreshed(new Date());
    } catch (error) {
      console.error(error);
      setSummaryError(true);
    } finally {
      setSummaryLoading(false);
    }
  }, [platform]);

  useEffect(() => {
    fetchInsightSummary();
  }, [fetchInsightSummary]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(() => {
        fetchInsightSummary();
      }, REFRESH_INTERVAL_MS);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [autoRefresh, fetchInsightSummary]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchInsightSummary();
    setRefreshing(false);
    toast("洞察数据已刷新", "success");
  };

  const getSeverity = (score: number): { level: SeverityLevel; label: string; color: string; bgClass: string } => {
    if (score >= 85) return { level: "high", label: "高潜力", color: "text-green-400", bgClass: "bg-green-500/10 border-green-500/30" };
    if (score >= 70) return { level: "medium", label: "值得关注", color: "text-yellow-400", bgClass: "bg-yellow-500/10 border-yellow-500/30" };
    return { level: "low", label: "观察中", color: "text-white/50", bgClass: "bg-white/5 border-white/10" };
  };

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  };

  return (
    <div className="container py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-3xl font-bold">
            <Flame className="h-7 w-7 text-orange-400" />
            智能洞察
          </h1>
          <p className="text-muted-foreground">基于12平台实时数据的趋势分析和爆款预测</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all ${
              autoRefresh
                ? "border-green-500/30 bg-green-500/10 text-green-400"
                : "border-white/10 text-white/40 hover:border-white/20 hover:text-white/60"
            }`}
            title={autoRefresh ? "自动刷新已开启" : "点击开启自动刷新"}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${autoRefresh ? "animate-spin" : ""}`} />
            {autoRefresh ? "每5分钟自动刷新" : "自动刷新"}
          </button>

          {/* Manual refresh */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
            className="border-white/10 text-white/50 hover:text-orange-400"
          >
            <RefreshCw className={`mr-1 h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "刷新中..." : "立即刷新"}
          </Button>
        </div>
      </div>

      {/* Platform Selector */}
      <Card className="border-white/5 bg-white/[0.02]">
        <CardContent className="flex flex-wrap items-center gap-4 p-4">
          <div className="flex items-center gap-2">
            <Globe className="h-4 w-4 text-white/40" />
            <span className="text-sm text-white/50">目标平台</span>
          </div>
          <Select value={platform} onValueChange={setPlatform}>
            <SelectTrigger className="w-[180px] border-white/10 bg-white/5 text-white/70">
              <SelectValue placeholder="选择平台" />
            </SelectTrigger>
            <SelectContent className="border-white/10 bg-zinc-900 text-white/80">
              {PLATFORMS.map((p) => (
                <SelectItem key={p} value={p} className="hover:bg-white/10 focus:bg-white/10">
                  {p}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {lastRefreshed && (
            <span className="ml-auto flex items-center gap-1 text-xs text-white/30">
              <Clock className="h-3 w-3" />
              上次刷新: {formatTime(lastRefreshed)}
            </span>
          )}
        </CardContent>
      </Card>

      {/* Insight Summary Cards */}
      {summaryLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="glass-card h-32 animate-pulse rounded-xl border-white/5 p-4">
              <div className="mb-2 h-3 w-1/2 rounded bg-white/10" />
              <div className="mb-3 h-6 w-1/3 rounded bg-white/10" />
              <div className="h-3 w-3/4 rounded bg-white/10" />
            </div>
          ))}
        </div>
      ) : summaryError ? (
        <Card className="border-red-500/20 bg-red-500/5">
          <CardContent className="flex flex-col items-center gap-3 py-6">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <p className="text-sm text-white/60">洞察摘要加载失败</p>
            <Button variant="outline" size="sm" onClick={handleRefresh} className="border-white/10">
              重试
            </Button>
          </CardContent>
        </Card>
      ) : summary ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {/* Trends Count */}
          <Card className="border-white/5 bg-white/[0.02]">
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10">
                  <Activity className="h-4 w-4 text-blue-400" />
                </div>
                <span className="text-sm text-white/50">趋势追踪</span>
              </div>
              <div className="text-2xl font-bold text-white/80">{summary.totalTrends}</div>
              <div className="mt-1 flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1">
                  <ArrowUpRight className="h-3 w-3 text-green-400" />
                  <span className="text-green-400">{summary.risingCount} 上升</span>
                </span>
                <span className="flex items-center gap-1">
                  <ArrowDownRight className="h-3 w-3 text-red-400" />
                  <span className="text-red-400">{summary.decliningCount} 下降</span>
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Top Prediction */}
          <Card className="border-white/5 bg-white/[0.02]">
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-500/10">
                  <Zap className="h-4 w-4 text-orange-400" />
                </div>
                <span className="text-sm text-white/50">最佳预测话题</span>
              </div>
              {summary.topPrediction ? (
                <>
                  <div className="text-lg font-bold text-white/80 truncate">{summary.topPrediction.topic}</div>
                  <Badge className={`mt-1.5 ${getSeverity(summary.topPrediction.viralScore).bgClass}`}>
                    <Flame className="mr-1 h-3 w-3" />
                    {summary.topPrediction.viralScore} 分 · {getSeverity(summary.topPrediction.viralScore).label}
                  </Badge>
                </>
              ) : (
                <div className="text-sm text-white/30">暂无预测数据</div>
              )}
            </CardContent>
          </Card>

          {/* Best Time Slot */}
          <Card className="border-white/5 bg-white/[0.02]">
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10">
                  <Clock className="h-4 w-4 text-purple-400" />
                </div>
                <span className="text-sm text-white/50">最佳发布时间</span>
              </div>
              {summary.bestTimeSlot ? (
                <>
                  <div className="text-lg font-bold text-white/80">{summary.bestTimeSlot.time}</div>
                  <Badge className={`mt-1.5 ${getSeverity(summary.bestTimeSlot.score).bgClass}`}>
                    <Sparkles className="mr-1 h-3 w-3" />
                    {summary.bestTimeSlot.score} 分
                  </Badge>
                </>
              ) : (
                <div className="text-sm text-white/30">暂无时段数据</div>
              )}
            </CardContent>
          </Card>

          {/* Platform Status */}
          <Card className="border-white/5 bg-white/[0.02]">
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-500/10">
                  <Target className="h-4 w-4 text-green-400" />
                </div>
                <span className="text-sm text-white/50">当前平台</span>
              </div>
              <div className="text-lg font-bold text-white/80">{platform}</div>
              <div className="mt-1 flex items-center gap-1.5 text-xs">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-green-400" />
                <span className="text-green-400/80">数据已同步</span>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}

      {/* Existing Insights Dashboard */}
      <InsightsDashboard />
    </div>
  );
}
