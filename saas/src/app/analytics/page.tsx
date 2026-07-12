"use client";

import { useState, useEffect, useCallback } from "react";
import { AnalyticsDashboard } from "@/components/analytics-dashboard";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  TrendingUp, Eye, Heart, MessageCircle, Share2,
  BarChart3, Activity, RefreshCw, Clock, Loader2, AlertCircle,
  Globe, Filter, Sparkles,
} from "lucide-react";
import { toast } from "@/components/toaster";

interface PlatformSummary {
  platform: string;
  count: number;
  totalViews: number;
  totalLikes: number;
  avgEngagement: number;
}

interface GlobalSummary {
  totalContent: number;
  totalViews: number;
  totalLikes: number;
  totalComments: number;
  totalShares: number;
  avgEngagement: number;
  platforms: Record<string, { count: number; views: number; likes: number }>;
}

const PLATFORMS = [
  { key: "all", label: "全部" },
  { key: "抖音", label: "抖音" },
  { key: "小红书", label: "小红书" },
  { key: "B站", label: "B站" },
  { key: "公众号", label: "公众号" },
  { key: "YouTube", label: "YouTube" },
  { key: "TikTok", label: "TikTok" },
  { key: "快手", label: "快手" },
  { key: "微博", label: "微博" },
  { key: "知乎", label: "知乎" },
  { key: "头条", label: "头条" },
];

const TIME_PERIODS = [
  { key: 7 as const, label: "7天" },
  { key: 30 as const, label: "30天" },
  { key: 90 as const, label: "90天" },
];

type TimePeriod = 7 | 30 | 90;

function formatNumber(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + "w";
  if (n >= 1000) return (n / 1000).toFixed(1) + "k";
  return n.toLocaleString();
}

export default function AnalyticsPage() {
  const [selectedPlatform, setSelectedPlatform] = useState("all");
  const [timePeriod, setTimePeriod] = useState<TimePeriod>(30);
  const [summary, setSummary] = useState<GlobalSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchSummary = useCallback(async () => {
    setSummaryLoading(true);
    setSummaryError(false);
    try {
      const [analyticsRes, platformsRes] = await Promise.all([
        fetch("/api/analytics/project/default"),
        fetch("/api/analytics"),
      ]);

      let totalContent = 0;
      let totalViews = 0;
      let totalLikes = 0;
      let totalComments = 0;
      let totalShares = 0;
      let avgEngagement = 0;

      if (analyticsRes.ok) {
        const data = await analyticsRes.json();
        totalContent = data.total_content || 0;
        totalViews = data.total_views || 0;
        totalLikes = data.total_likes || 0;
        totalComments = data.total_comments || 0;
        totalShares = data.total_shares || 0;
        avgEngagement = data.avg_engagement || 0;
      }

      let platforms: Record<string, { count: number; views: number; likes: number }> = {};
      if (platformsRes.ok) {
        const data = await platformsRes.json();
        platforms = data.platforms || {};
      }

      setSummary({
        totalContent,
        totalViews,
        totalLikes,
        totalComments,
        totalShares,
        avgEngagement,
        platforms,
      });
      setLastUpdated(new Date());
    } catch (error) {
      console.error(error);
      setSummaryError(true);
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchSummary();
    setRefreshing(false);
    toast("数据已刷新", "success");
  };

  const statCards = summary
    ? [
        { label: "总内容数", value: summary.totalContent.toLocaleString(), icon: BarChart3, color: "text-blue-400", bgColor: "bg-blue-500/10" },
        { label: "总曝光", value: formatNumber(summary.totalViews), icon: Eye, color: "text-purple-400", bgColor: "bg-purple-500/10" },
        { label: "总点赞", value: formatNumber(summary.totalLikes), icon: Heart, color: "text-red-400", bgColor: "bg-red-500/10" },
        { label: "总评论", value: formatNumber(summary.totalComments), icon: MessageCircle, color: "text-green-400", bgColor: "bg-green-500/10" },
        { label: "总分享", value: formatNumber(summary.totalShares), icon: Share2, color: "text-orange-400", bgColor: "bg-orange-500/10" },
        { label: "平均互动率", value: `${summary.avgEngagement}%`, icon: TrendingUp, color: "text-pink-400", bgColor: "bg-pink-500/10" },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between px-6 pt-6">
        <div>
          <h1 className="flex items-center gap-2 text-3xl font-bold">
            <Activity className="h-7 w-7 text-orange-400" />
            数据分析
          </h1>
          <p className="text-muted-foreground">全面追踪你的内容表现与趋势</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Last Updated */}
          {lastUpdated && (
            <span className="flex items-center gap-1 text-xs text-white/40">
              <Clock className="h-3 w-3" />
              更新于 {lastUpdated.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </span>
          )}

          {/* Time Period Selector */}
          <div className="flex overflow-hidden rounded-lg border border-white/10">
            {TIME_PERIODS.map((p) => (
              <button
                key={p.key}
                onClick={() => setTimePeriod(p.key)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                  timePeriod === p.key
                    ? "bg-orange-500/20 text-orange-400"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Refresh */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
            className="border-white/10 text-white/50 hover:text-orange-400"
          >
            <RefreshCw className={`mr-1 h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "刷新中..." : "刷新"}
          </Button>
        </div>
      </div>

      {/* Summary Stats Cards */}
      {summaryLoading ? (
        <div className="grid gap-4 px-6 md:grid-cols-3 lg:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="glass-card h-24 animate-pulse rounded-xl border-white/5 p-4">
              <div className="mb-2 h-3 w-1/2 rounded bg-white/10" />
              <div className="h-6 w-1/3 rounded bg-white/10" />
            </div>
          ))}
        </div>
      ) : summaryError ? (
        <div className="px-6">
          <Card className="border-red-500/20 bg-red-500/5">
            <CardContent className="flex flex-col items-center gap-3 py-8">
              <AlertCircle className="h-8 w-8 text-red-400" />
              <p className="text-sm text-white/60">汇总数据加载失败</p>
              <Button variant="outline" size="sm" onClick={handleRefresh} className="border-white/10">
                重试
              </Button>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="grid gap-4 px-6 md:grid-cols-3 lg:grid-cols-6">
          {statCards.map((s) => (
            <Card key={s.label} className="glass-card border-white/5">
              <CardContent className="flex items-center gap-3 p-4">
                <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${s.bgColor}`}>
                  <s.icon className={`h-5 w-5 ${s.color}`} />
                </div>
                <div>
                  <div className="text-xl font-bold">{s.value}</div>
                  <div className="text-xs text-white/40">{s.label}</div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Platform Filter Tabs */}
      <div className="px-6">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="h-4 w-4 text-white/40" />
          <span className="text-sm text-white/50">平台筛选</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {PLATFORMS.map((p) => (
            <Badge
              key={p.key}
              variant={selectedPlatform === p.key ? "default" : "outline"}
              className={`cursor-pointer transition-all ${
                selectedPlatform === p.key
                  ? "bg-orange-500/20 text-orange-400 border-orange-500/30"
                  : "border-white/10 text-white/40 hover:border-white/20 hover:text-white/60"
              }`}
              onClick={() => setSelectedPlatform(p.key)}
            >
              {p.label}
              {summary?.platforms[p.key] && p.key !== "all" && (
                <span className="ml-1 text-white/30">
                  ({summary.platforms[p.key].count})
                </span>
              )}
            </Badge>
          ))}
        </div>
      </div>

      {/* Platform-specific summary when a platform is selected */}
      {selectedPlatform !== "all" && summary?.platforms[selectedPlatform] && (
        <div className="px-6">
          <Card className="border-orange-500/20 bg-gradient-to-r from-orange-500/5 to-transparent">
            <CardContent className="flex flex-wrap items-center gap-6 p-4">
              <div className="flex items-center gap-2">
                <Globe className="h-5 w-5 text-orange-400" />
                <span className="font-medium text-white/70">{selectedPlatform}</span>
              </div>
              <div className="flex items-center gap-1 text-sm">
                <span className="text-white/40">内容数</span>
                <span className="font-semibold text-white/70">{summary.platforms[selectedPlatform].count}</span>
              </div>
              <div className="flex items-center gap-1 text-sm">
                <Eye className="h-3.5 w-3.5 text-blue-400" />
                <span className="text-white/40">曝光</span>
                <span className="font-semibold text-white/70">{formatNumber(summary.platforms[selectedPlatform].views)}</span>
              </div>
              <div className="flex items-center gap-1 text-sm">
                <Heart className="h-3.5 w-3.5 text-red-400" />
                <span className="text-white/40">点赞</span>
                <span className="font-semibold text-white/70">{formatNumber(summary.platforms[selectedPlatform].likes)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Existing Analytics Dashboard */}
      <AnalyticsDashboard />
    </div>
  );
}
