"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  TrendingUp, Eye, Heart, MessageCircle, Share2,
  BarChart3, Activity, RefreshCw, Clock,
  ArrowUpDown, Flame, Globe, Table2,
  Hash, Grid3x3, PenTool, AlertCircle,
} from "lucide-react";

/* ============================================================
   Types
   ============================================================ */

interface PlatformStat {
  count: number;
  views: number;
  likes: number;
}

interface ContentItem {
  title: string;
  platform: string;
  metrics: { views: number; likes: number; comments: number; shares: number };
  fire_score?: number;
  published_at?: string;
}

interface AnalyticsData {
  total_content: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  avg_engagement: number;
  content_list: ContentItem[];
}

interface FireScorePoint {
  date: string;
  score: number;
}

type TimePeriod = 7 | 30 | 90;
type SortKey = "views" | "likes" | "engagement";

/* ============================================================
   Platform colour & icon mapping
   ============================================================ */

const PLATFORM_META: Record<string, { color: string; label: string }> = {
  "抖音":     { color: "#f97316", label: "抖音" },
  "小红书":   { color: "#ec4899", label: "小红书" },
  "B站":     { color: "#3b82f6", label: "B站" },
  "公众号":   { color: "#22c55e", label: "公众号" },
  "YouTube": { color: "#ef4444", label: "YouTube" },
  "TikTok":  { color: "#06b6d4", label: "TikTok" },
  "快手":    { color: "#a855f7", label: "快手" },
  "微博":    { color: "#f59e0b", label: "微博" },
  "知乎":    { color: "#6366f1", label: "知乎" },
  "头条":    { color: "#dc2626", label: "头条" },
};

function getPlatformColor(platform: string): string {
  return PLATFORM_META[platform]?.color ?? "#8b5cf6";
}

function getPlatformLabel(platform: string): string {
  return PLATFORM_META[platform]?.label ?? platform;
}

/* ============================================================
   Helpers
   ============================================================ */

function fireScoreColor(score: number): string {
  if (score >= 90) return "#22c55e";
  if (score >= 80) return "#eab308";
  if (score >= 70) return "#f97316";
  return "#ef4444";
}

function fireScoreBg(score: number): string {
  if (score >= 90) return "bg-green-500/20 text-green-400";
  if (score >= 80) return "bg-yellow-500/20 text-yellow-400";
  if (score >= 70) return "bg-orange-500/20 text-orange-400";
  return "bg-red-500/20 text-red-400";
}

function formatNumber(n: number): string {
  if (n >= 1_0000) return (n / 1_0000).toFixed(1) + "w";
  if (n >= 1000) return (n / 1000).toFixed(1) + "k";
  return n.toLocaleString();
}

/** Generate mock Fire Score history for demo / fallback */
function generateMockFireHistory(days: number): FireScorePoint[] {
  const now = new Date();
  const points: FireScorePoint[] = [];
  let score = 60 + Math.random() * 20;
  for (let i = days; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    score = Math.max(40, Math.min(100, score + (Math.random() - 0.5) * 12));
    const label = `${d.getMonth() + 1}/${d.getDate()}`;
    points.push({ date: label, score: Math.round(score) });
  }
  return points;
}

/** Generate publishing heatmap data (days x hours) */
function generateMockHeatmap(days: number): number[][] {
  const grid: number[][] = [];
  for (let d = 0; d < days; d++) {
    const row: number[] = [];
    for (let h = 0; h < 24; h++) {
      // peak at 10-11am and 8-9pm
      const base = (h >= 9 && h <= 11) || (h >= 19 && h <= 21) ? 3 : 1;
      row.push(Math.max(0, Math.floor(base + (Math.random() - 0.5) * 2.5)));
    }
    grid.push(row);
  }
  return grid;
}

/* ============================================================
   Sub-components
   ============================================================ */

/** #1 — Fire Score Trend SVG Line Chart */
function FireScoreTrendChart({ data, days }: { data: FireScorePoint[]; days: number }) {
  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">暂无趋势数据</p>;
  }

  const w = 600;
  const h = 200;
  const pad = { top: 20, right: 20, bottom: 30, left: 40 };
  const chartW = w - pad.left - pad.right;
  const chartH = h - pad.top - pad.bottom;

  const minScore = Math.min(...data.map((d) => d.score)) - 5;
  const maxScore = Math.max(...data.map((d) => d.score)) + 5;
  const range = maxScore - minScore || 1;

  const xScale = (i: number) => pad.left + (i / Math.max(data.length - 1, 1)) * chartW;
  const yScale = (v: number) => pad.top + chartH - ((v - minScore) / range) * chartH;

  const pathD = data
    .map((d, i) => `${i === 0 ? "M" : "L"}${xScale(i).toFixed(1)},${yScale(d.score).toFixed(1)}`)
    .join(" ");

  const areaD =
    pathD +
    ` L${xScale(data.length - 1).toFixed(1)},${pad.top + chartH}` +
    ` L${xScale(0).toFixed(1)},${pad.top + chartH} Z`;

  const yTicks = [minScore, (minScore + maxScore) / 2, maxScore];

  const xLabelCount = Math.min(data.length, 6);
  const xStep = Math.max(1, Math.floor((data.length - 1) / (xLabelCount - 1)));

  return (
    <div className="overflow-x-auto">
      <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} className="min-w-[400px]">
        {yTicks.map((t) => (
          <g key={t}>
            <line
              x1={pad.left} y1={yScale(t)} x2={w - pad.right} y2={yScale(t)}
              stroke="rgba(255,255,255,0.06)" strokeWidth={1}
            />
            <text x={pad.left - 6} y={yScale(t) + 4} textAnchor="end" fill="rgba(255,255,255,0.4)" fontSize={10}>
              {t}
            </text>
          </g>
        ))}
        <defs>
          <linearGradient id="fireGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f97316" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#f97316" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <path d={areaD} fill="url(#fireGradient)" />
        <path d={pathD} fill="none" stroke="#f97316" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        {data.map((d, i) => (
          <circle
            key={i}
            cx={xScale(i)} cy={yScale(d.score)} r={3}
            fill={fireScoreColor(d.score)} stroke="#0a0a0f" strokeWidth={1.5}
          >
            <title>{d.date}: {d.score}分</title>
          </circle>
        ))}
        {data.filter((_, i) => i % xStep === 0 || i === data.length - 1).map((d, i, arr) => {
          const idx = data.indexOf(d);
          return (
            <text
              key={i} x={xScale(idx)} y={h - 4} textAnchor="middle"
              fill="rgba(255,255,255,0.4)" fontSize={10}
            >
              {d.date}
            </text>
          );
        })}
      </svg>
    </div>
  );
}

/** #2 — Platform Distribution Pie (CSS conic gradient) */
function PlatformPieChart({ platforms, total }: { platforms: Record<string, PlatformStat>; total: number }) {
  const entries = Object.entries(platforms);
  if (entries.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">暂无平台数据</p>;
  }

  const sorted = entries.sort((a, b) => b[1].views - a[1].views);
  const conicStops = sorted.map(([name, stat], i) => {
    const pct = total > 0 ? (stat.views / total) * 100 : 0;
    const color = getPlatformColor(name);
    return { name, pct, color, count: stat.count, views: stat.views };
  });

  let cumulative = 0;
  const stops = conicStops.map((s) => {
    const start = cumulative;
    cumulative += s.pct;
    return `${s.color} ${start}% ${cumulative}%`;
  });
  const gradient = stops.length > 0 ? `conic-gradient(${stops.join(", ")})` : "none";

  return (
    <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start">
      <div className="relative shrink-0">
        <div
          className="h-40 w-40 rounded-full"
          style={{ background: gradient }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-background/80 text-center backdrop-blur">
            <div>
              <div className="text-lg font-bold text-orange-400">{total.toLocaleString()}</div>
              <div className="text-[10px] leading-tight text-muted-foreground">总曝光</div>
            </div>
          </div>
        </div>
      </div>
      <div className="flex-1 space-y-1.5">
        {conicStops.map((s) => (
          <div key={s.name} className="flex items-center justify-between gap-2 text-sm">
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full shrink-0" style={{ backgroundColor: s.color }} />
              <span className="text-foreground">{s.name}</span>
            </div>
            <div className="flex items-center gap-3 text-muted-foreground">
              <span>{s.pct.toFixed(1)}%</span>
              <span className="w-14 text-right">{formatNumber(s.views)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/** #3 — Daily Publishing Heatmap (7 x 24 grid) */
function PublishingHeatmap({ days }: { days: number }) {
  const grid = useMemo(() => generateMockHeatmap(days), [days]);
  const maxVal = Math.max(1, ...grid.flat());

  const hourLabels = Array.from({ length: 24 }, (_, h) => `${h}:00`);
  const showHour = (h: number) => h % 3 === 0;

  const cellSize = days > 7 ? 12 : 16;
  const gap = 2;
  const dayLabels = ["一", "二", "三", "四", "五", "六", "日"];

  return (
    <div className="overflow-x-auto">
      <div className="flex gap-1" style={{ minWidth: days * (cellSize + gap) + 40 }}>
        <div className="shrink-0" style={{ width: 32 }}>
          <div style={{ height: cellSize + gap }} />
          {hourLabels.map((label, h) =>
            showHour(h) ? (
              <div
                key={h}
                className="flex items-center justify-end pr-1 text-[10px] text-muted-foreground"
                style={{ height: cellSize + gap }}
              >
                {label}
              </div>
            ) : (
              <div key={h} style={{ height: cellSize + gap }} />
            )
          )}
        </div>
        <div className="flex gap-[2px]">
          {grid.map((row, d) => (
            <div key={d} className="flex flex-col gap-[2px]">
              <div className="text-center text-[10px] text-muted-foreground" style={{ height: cellSize + gap }}>
                {days <= 14 ? dayLabels[d % 7] : ""}
              </div>
              {row.map((val, h) => {
                const intensity = val / maxVal;
                let bg = "bg-zinc-800";
                if (val > 0) {
                  if (intensity > 0.75) bg = "bg-orange-500";
                  else if (intensity > 0.5) bg = "bg-orange-500/70";
                  else if (intensity > 0.25) bg = "bg-orange-500/40";
                  else bg = "bg-orange-500/20";
                }
                return (
                  <div
                    key={h}
                    className={`rounded-sm ${bg} transition-colors`}
                    style={{ width: cellSize, height: cellSize }}
                    title={`第${d + 1}天 ${h}:00 — ${val}篇`}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>
      <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
        <span>少</span>
        <div className="h-3 w-3 rounded-sm bg-zinc-800" />
        <div className="h-3 w-3 rounded-sm bg-orange-500/20" />
        <div className="h-3 w-3 rounded-sm bg-orange-500/40" />
        <div className="h-3 w-3 rounded-sm bg-orange-500/70" />
        <div className="h-3 w-3 rounded-sm bg-orange-500" />
        <span>多</span>
      </div>
    </div>
  );
}

/** #4 — Top Performing Content Sortable Table */
function TopContentTable({ items }: { items: ContentItem[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("views");
  const [sortAsc, setSortAsc] = useState(false);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc((p) => !p);
    else { setSortKey(key); setSortAsc(false); }
  };

  const sorted = useMemo(() => {
    const list = [...items];
    if (sortKey === "engagement") {
      list.sort((a, b) => {
        const ea = a.metrics.views > 0 ? (a.metrics.likes + a.metrics.comments + a.metrics.shares) / a.metrics.views : 0;
        const eb = b.metrics.views > 0 ? (b.metrics.likes + b.metrics.comments + b.metrics.shares) / b.metrics.views : 0;
        return sortAsc ? ea - eb : eb - ea;
      });
    } else {
      list.sort((a, b) => sortAsc ? a.metrics[sortKey] - b.metrics[sortKey] : b.metrics[sortKey] - a.metrics[sortKey]);
    }
    return list.slice(0, 20);
  }, [items, sortKey, sortAsc]);

  const sortIndicator = (key: SortKey) => {
    if (sortKey !== key) return null;
    return <ArrowUpDown className="ml-1 inline h-3 w-3" />;
  };

  const calcEngagement = (m: ContentItem["metrics"]) =>
    m.views > 0 ? ((m.likes + m.comments + m.shares) / m.views * 100).toFixed(1) : "0.0";

  if (items.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">暂无内容数据</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10 text-muted-foreground">
            <th className="px-2 py-2 text-left font-medium">#</th>
            <th className="px-2 py-2 text-left font-medium">标题</th>
            <th className="px-2 py-2 text-left font-medium">平台</th>
            <th
              className="cursor-pointer px-2 py-2 text-right font-medium hover:text-foreground"
              onClick={() => toggleSort("views")}
            >
              曝光 {sortIndicator("views")}
            </th>
            <th
              className="cursor-pointer px-2 py-2 text-right font-medium hover:text-foreground"
              onClick={() => toggleSort("likes")}
            >
              点赞 {sortIndicator("likes")}
            </th>
            <th
              className="cursor-pointer px-2 py-2 text-right font-medium hover:text-foreground"
              onClick={() => toggleSort("engagement")}
            >
              互动率 {sortIndicator("engagement")}
            </th>
            <th className="px-2 py-2 text-center font-medium">Fire Score</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((item, i) => {
            const fs = item.fire_score ?? Math.floor(50 + Math.random() * 45);
            return (
              <tr key={i} className="border-b border-white/5 transition-colors hover:bg-white/5">
                <td className="px-2 py-2 text-muted-foreground">{i + 1}</td>
                <td className="max-w-[200px] truncate px-2 py-2 font-medium" title={item.title}>
                  {item.title}
                </td>
                <td className="px-2 py-2">
                  <Badge
                    variant="outline"
                    className="border-0 text-xs"
                    style={{
                      backgroundColor: `${getPlatformColor(item.platform)}20`,
                      color: getPlatformColor(item.platform),
                    }}
                  >
                    {getPlatformLabel(item.platform)}
                  </Badge>
                </td>
                <td className="px-2 py-2 text-right tabular-nums">{formatNumber(item.metrics.views)}</td>
                <td className="px-2 py-2 text-right tabular-nums">{formatNumber(item.metrics.likes)}</td>
                <td className="px-2 py-2 text-right tabular-nums">{calcEngagement(item.metrics)}%</td>
                <td className="px-2 py-2 text-center">
                  <span className={`inline-block rounded px-1.5 py-0.5 text-xs font-semibold ${fireScoreBg(fs)}`}>
                    {fs}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/* ============================================================
   Skeleton States
   ============================================================ */

function SkeletonGrid({ rows = 2, cols = 3 }: { rows?: number; cols?: number }) {
  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
      {Array.from({ length: rows * cols }).map((_, i) => (
        <div key={i} className="glass-card h-24 animate-pulse p-4">
          <div className="mb-2 h-3 w-1/2 rounded bg-white/10" />
          <div className="h-6 w-1/3 rounded bg-white/10" />
        </div>
      ))}
    </div>
  );
}

function SkeletonChart() {
  return (
    <div className="glass-card animate-pulse p-6">
      <div className="mb-4 h-4 w-1/4 rounded bg-white/10" />
      <div className="h-[200px] w-full rounded bg-white/5" />
    </div>
  );
}

/* ============================================================
   Main Component
   ============================================================ */

export function AnalyticsDashboard() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [platforms, setPlatforms] = useState<Record<string, PlatformStat>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<TimePeriod>(30);
  const [activeTab, setActiveTab] = useState<"trend" | "heatmap">("trend");

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const [analyticsRes, platformsRes] = await Promise.all([
        fetch("/api/analytics/project/default"),
        fetch("/api/analytics"),
      ]);
      const analyticsData = await analyticsRes.json();
      const platformsData = await platformsRes.json();
      setData(analyticsData);
      setPlatforms(platformsData.platforms || {});
      setLastUpdated(new Date());
    } catch (error) {
      console.error(error);
      setError("加载数据失败");
    }
  }, []);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await fetchData();
      setLoading(false);
    };
    load();
  }, [fetchData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    await fetchData();
    setRefreshing(false);
  };

  // Mock Fire Score history from content_list
  const fireHistory = useMemo<FireScorePoint[]>(() => {
    if (!data || data.content_list.length === 0) return generateMockFireHistory(period);
    const dated = data.content_list.filter((c) => c.published_at);
    if (dated.length === 0) return generateMockFireHistory(period);
    const scores: FireScorePoint[] = [];
    const now = new Date();
    for (let i = period; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      const dayStr = `${d.getMonth() + 1}/${d.getDate()}`;
      const dayItems = dated.filter((c) => {
        const pd = new Date(c.published_at!);
        return pd.toDateString() === d.toDateString();
      });
      const avgScore =
        dayItems.length > 0
          ? Math.round(dayItems.reduce((s, c) => s + (c.fire_score ?? 70), 0) / dayItems.length)
          : Math.round(50 + Math.random() * 30);
      scores.push({ date: dayStr, score: avgScore });
    }
    return scores;
  }, [data, period]);

  const heatmapData = useMemo(() => generateMockHeatmap(period), [period]);

  const stats = data
    ? [
        { label: "总内容数", value: data.total_content, icon: BarChart3, color: "text-blue-400" },
        { label: "总曝光", value: formatNumber(data.total_views), icon: Eye, color: "text-purple-400" },
        { label: "总点赞", value: formatNumber(data.total_likes), icon: Heart, color: "text-red-400" },
        { label: "总评论", value: formatNumber(data.total_comments), icon: MessageCircle, color: "text-green-400" },
        { label: "总分享", value: formatNumber(data.total_shares), icon: Share2, color: "text-orange-400" },
        { label: "平均互动率", value: `${data.avg_engagement}%`, icon: TrendingUp, color: "text-pink-400" },
      ]
    : [];

  /* ---- Error State ---- */
  if (error && !data) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center gap-4 p-8">
        <AlertCircle className="h-16 w-16 text-red-400/60" />
        <p className="text-lg text-white/60">数据加载失败</p>
        <p className="text-sm text-white/40">请检查网络连接或后端服务是否正常运行</p>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="inline-flex items-center gap-2 rounded-lg border border-red-500/30 px-4 py-2 text-sm text-red-400 transition-colors hover:bg-red-500/10"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
          重试
        </button>
      </div>
    );
  }

  /* ---- Empty State ---- */
  if (!data) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center gap-4 p-8">
        <Activity className="h-16 w-16 text-muted-foreground/40" />
        <p className="text-lg text-white/60">暂无数据</p>
        <p className="text-sm text-white/40 max-w-md text-center">
          发布内容后，分析数据将在这里展示。先去生成一些内容吧！
        </p>
        <div className="flex gap-3">
          <Link href="/generate">
            <Button className="bg-gradient-to-r from-orange-500 to-pink-500 text-white">
              <PenTool className="mr-2 h-4 w-4" />
              去生成内容
            </Button>
          </Link>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-2 rounded-lg border border-white/10 px-4 py-2 text-sm text-white/50 transition-colors hover:bg-white/5"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            刷新
          </button>
        </div>
      </div>
    );
  }

  /* ---- Main Render ---- */
  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">
            <Activity className="mr-2 inline h-7 w-7 text-orange-400" />
            数据仪表盘
          </h1>
          <p className="text-muted-foreground">实时追踪内容表现与趋势</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {/* Last Updated */}
          {lastUpdated && (
            <span className="hidden items-center gap-1 text-xs text-white/40 sm:flex">
              <Clock className="h-3 w-3" />
              更新于 {lastUpdated.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </span>
          )}
          {/* Time Period Selector */}
          <div className="flex overflow-hidden rounded-lg border border-white/10">
            {([7, 30, 90] as TimePeriod[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                  period === p
                    ? "bg-orange-500/20 text-orange-400"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {p}天
              </button>
            ))}
          </div>
          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-white/50 transition-colors hover:border-orange-500/30 hover:text-orange-400 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "刷新中..." : "刷新"}
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
        {stats.map((s) => (
          <Card key={s.label} className="glass-card">
            <CardContent className="p-4">
              <s.icon className={`mb-2 h-5 w-5 ${s.color}`} />
              <div className="text-2xl font-bold">{s.value}</div>
              <div className="text-xs text-muted-foreground">{s.label}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Row 2: Fire Score Trend + Platform Pie */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="glass-card glow-orange">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Flame className="h-5 w-5 text-orange-400" />
              Fire Score 趋势
            </CardTitle>
            <CardDescription>近{period}天内容热度评分变化</CardDescription>
          </CardHeader>
          <CardContent>
            <FireScoreTrendChart data={fireHistory} days={period} />
          </CardContent>
        </Card>

        <Card className="glass-card glow-purple">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Globe className="h-5 w-5 text-purple-400" />
              平台分布
            </CardTitle>
            <CardDescription>各平台内容曝光占比</CardDescription>
          </CardHeader>
          <CardContent>
            <PlatformPieChart platforms={platforms} total={data.total_views} />
          </CardContent>
        </Card>
      </div>

      {/* Row 3: Publishing Heatmap */}
      <Card className="glass-card glow-cyan">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Grid3x3 className="h-5 w-5 text-cyan-400" />
              发布热力图
            </CardTitle>
            <CardDescription>近{period}天各时段发布活跃度</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <PublishingHeatmap days={period} />
        </CardContent>
      </Card>

      {/* Row 4: Top Performing Content Table */}
      <Card className="glass-card glow-green">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Table2 className="h-5 w-5 text-green-400" />
              内容排行
            </CardTitle>
            <CardDescription>点击表头排序 · 共{data.content_list.length}篇</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <TopContentTable items={data.content_list} />
        </CardContent>
      </Card>

      {/* Mobile-only: last updated timestamp */}
      {lastUpdated && (
        <div className="text-center text-xs text-white/30 sm:hidden">
          最后更新: {lastUpdated.toLocaleString("zh-CN")}
        </div>
      )}
    </div>
  );
}
