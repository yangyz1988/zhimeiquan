"use client";

import { useState, useEffect } from "react";
import { TrendingUp, Flame, Search, RefreshCw, ExternalLink, Clock } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { toast } from "@/components/toaster";
import { apiFetch } from "@/lib/api";

interface TrendEvent {
  id: string;
  title: string;
  summary?: string;
  source_platform: string;
  category?: string;
  heat_score: number;
  heat_trend: string;
  mention_count: number;
  first_seen_at: string;
  last_seen_at: string;
  keywords?: string[];
}

const platforms = ["全部", "抖音", "小红书", "B站", "微博", "知乎", "头条"];
const trends = ["RISING", "STABLE", "PEAKING", "DECLINING"];

export default function TrendsPage() {
  const [events, setEvents] = useState<TrendEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [platform, setPlatform] = useState("全部");
  const [trend, setTrend] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadTrends();
  }, [platform, trend]);

  const loadTrends = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (platform !== "全部") params.set("platform", platform);
      if (trend) params.set("trend", trend);

      const result = await apiFetch<{ events: TrendEvent[] }>(`/api/trends?${params}`);
      if (result.ok && result.data) setEvents(result.data.events);
    } catch {
      setEvents([
        { id: "1", title: "AI 换脸技术争议", source_platform: "抖音", heat_score: 89.5, heat_trend: "RISING", mention_count: 15000, first_seen_at: new Date().toISOString(), last_seen_at: new Date().toISOString(), keywords: ["AI", "换脸", "安全"] },
        { id: "2", title: "短剧爆火现象分析", source_platform: "小红书", heat_score: 75.2, heat_trend: "STABLE", mention_count: 8000, first_seen_at: new Date().toISOString(), last_seen_at: new Date().toISOString(), keywords: ["短剧", "流量", "变现"] },
        { id: "3", title: "新能源汽车价格战", source_platform: "微博", heat_score: 68.3, heat_trend: "PEAKING", mention_count: 5000, first_seen_at: new Date().toISOString(), last_seen_at: new Date().toISOString(), keywords: ["新能源", "价格", "竞争"] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    try {
      const result = await apiFetch("/api/trends", {
        method: "POST",
        body: { action: "scan" },
      });
      if (result.ok) {
        toast("热点扫描已触发", "success");
        loadTrends();
      }
    } catch {
      toast("扫描失败", "error");
    }
  };

  const getTrendBadge = (t: string) => {
    const map: Record<string, { variant: "default" | "secondary" | "destructive"; label: string }> = {
      RISING: { variant: "default", label: "上升" },
      STABLE: { variant: "secondary", label: "稳定" },
      PEAKING: { variant: "default", label: "峰值" },
      DECLINING: { variant: "destructive", label: "下降" },
    };
    const { variant, label } = map[t] || { variant: "secondary", label: t };
    return <Badge variant={variant}>{label}</Badge>;
  };

  const getHeatColor = (score: number) => {
    if (score >= 80) return "text-red-500";
    if (score >= 60) return "text-orange-500";
    if (score >= 40) return "text-yellow-500";
    return "text-muted-foreground";
  };

  const filtered = events.filter(e =>
    e.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">热点追踪</h1>
          <p className="text-muted-foreground">实时追踪全平台热点事件</p>
        </div>
        <Button onClick={handleScan}>
          <RefreshCw className="w-4 h-4 mr-2" />
          扫描热点
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="搜索热点..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          {platforms.map(p => (
            <Button
              key={p}
              variant={platform === p ? "default" : "outline"}
              size="sm"
              onClick={() => setPlatform(p)}
            >
              {p}
            </Button>
          ))}
        </div>
        <select
          className="flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
          value={trend}
          onChange={e => setTrend(e.target.value)}
        >
          <option value="">全部趋势</option>
          {trends.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      {/* Events Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full text-center py-12 text-muted-foreground">加载中...</div>
        ) : filtered.length === 0 ? (
          <div className="col-span-full text-center py-12 text-muted-foreground">
            <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>暂无热点事件</p>
          </div>
        ) : (
          filtered.map(event => (
            <Card key={event.id} className="hover:shadow-md transition cursor-pointer">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-lg line-clamp-2">{event.title}</CardTitle>
                  {getTrendBadge(event.heat_trend)}
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Badge variant="outline">{event.source_platform}</Badge>
                  <Clock className="w-3 h-3" />
                  {new Date(event.last_seen_at).toLocaleDateString()}
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4 mb-3">
                  <div className="flex items-center gap-1">
                    <Flame className={`w-5 h-5 ${getHeatColor(event.heat_score)}`} />
                    <span className={`text-lg font-bold ${getHeatColor(event.heat_score)}`}>
                      {event.heat_score.toFixed(1)}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {event.mention_count.toLocaleString()} 次提及
                  </div>
                </div>
                {event.keywords && event.keywords.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {event.keywords.slice(0, 5).map(kw => (
                      <Badge key={kw} variant="secondary" className="text-xs">{kw}</Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}