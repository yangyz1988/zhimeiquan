"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  Clock,
  Target,
  Loader2,
  Sparkles,
} from "lucide-react";
import { toast } from "@/components/toaster";

const PLATFORMS = [
  "抖音",
  "小红书",
  "B站",
  "公众号",
  "YouTube",
  "TikTok",
  "快手",
  "微博",
  "知乎",
  "头条",
];

interface Trend {
  type: string;
  name: string;
  count: number;
  direction: string;
}

interface Prediction {
  topic: string;
  viral_score: number;
  reason: string;
  suggested_hook: string;
}

interface Recommendation {
  hook_type: string;
  best_duration: number;
  title_templates: string[];
  best_practices: string[];
}

interface TimeSlot {
  time: string;
  score: number;
  reason: string;
}

export function InsightsDashboard() {
  const [platform, setPlatform] = useState("抖音");
  const [trends, setTrends] = useState<Trend[]>([]);
  const [hotTopics, setHotTopics] = useState<string[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
  const [recommendation, setRecommendation] = useState("");
  const [loading, setLoading] = useState(true);

  const [topic, setTopic] = useState("");
  const [recData, setRecData] = useState<Recommendation | null>(null);
  const [recLoading, setRecLoading] = useState(false);

  useEffect(() => {
    fetchAllData();
  }, [platform]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const encoded = encodeURIComponent(platform);
      const [trendsRes, predictRes, timeRes] = await Promise.all([
        fetch(`/api/insights/trends/${encoded}`),
        fetch(`/api/insights/predict/${encoded}`),
        fetch(`/api/insights/posting-time/${encoded}`),
      ]);
      const trendsData = await trendsRes.json();
      const predictData = await predictRes.json();
      const timeData = await timeRes.json();

      setTrends(trendsData.trends || []);
      setHotTopics(trendsData.hot_topics || []);
      setPredictions(predictData.predictions || []);
      setTimeSlots(timeData.time_slots || []);
      setRecommendation(timeData.recommendation || "");
    } catch {
      toast("加载洞察数据失败", "error");
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    if (!topic.trim()) return;
    setRecLoading(true);
    try {
      const res = await fetch("/api/insights/recommendations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, platform }),
      });
      const data = await res.json();
      setRecData(data);
    } catch {
      toast("获取建议失败", "error");
    } finally {
      setRecLoading(false);
    }
  };

  const directionIcon = (dir: string) => {
    if (dir === "rising") return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (dir === "declining") return <TrendingDown className="h-4 w-4 text-red-500" />;
    return <Minus className="h-4 w-4 text-muted-foreground" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-orange-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">智能洞察</h1>
        <p className="text-muted-foreground">基于12平台数据的趋势分析和爆款预测</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {PLATFORMS.map((p) => (
          <Badge
            key={p}
            variant={platform === p ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => setPlatform(p)}
          >
            {p}
          </Badge>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-orange-500" />
              趋势分析
            </CardTitle>
            <CardDescription>{platform} 热门钩子模式</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {trends.length === 0 ? (
              <p className="text-sm text-muted-foreground">暂无趋势数据</p>
            ) : (
              trends.map((t, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {directionIcon(t.direction)}
                    <span className="text-sm font-medium">{t.name}</span>
                  </div>
                  <Badge variant="secondary">{t.count} 次</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-orange-500" />
              爆款预测
            </CardTitle>
            <CardDescription>{platform} 潜在爆款话题</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {predictions.length === 0 ? (
              <p className="text-sm text-muted-foreground">暂无预测数据</p>
            ) : (
              predictions.map((p, i) => (
                <div key={i} className="rounded-lg border p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{p.topic}</span>
                    <Badge className="bg-orange-500">{p.viral_score}分</Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {p.reason} · 建议使用{p.suggested_hook}
                  </p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-orange-500" />
            最佳发布时机
          </CardTitle>
          {recommendation && (
            <CardDescription>{recommendation}</CardDescription>
          )}
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-3">
            {timeSlots.map((slot, i) => (
              <div key={i} className="rounded-lg border p-3 text-center">
                <div className="text-lg font-bold">{slot.time}</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  {slot.reason}
                </div>
                <div className="mt-2">
                  <Badge variant={slot.score >= 90 ? "default" : "secondary"}>
                    {slot.score}分
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-orange-500" />
            内容建议
          </CardTitle>
          <CardDescription>输入主题，获取针对性的内容策略建议</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="输入内容主题"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchRecommendations()}
            />
            <Button onClick={fetchRecommendations} disabled={recLoading}>
              {recLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
            </Button>
          </div>
          {recData && (
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border p-3">
                <div className="text-sm font-medium text-muted-foreground">
                  推荐钩子类型
                </div>
                <div className="mt-1 text-lg font-bold text-orange-500">
                  {recData.hook_type}
                </div>
              </div>
              <div className="rounded-lg border p-3">
                <div className="text-sm font-medium text-muted-foreground">
                  推荐时长
                </div>
                <div className="mt-1 text-lg font-bold text-orange-500">
                  {recData.best_duration}秒
                </div>
              </div>
              {recData.title_templates.length > 0 && (
                <div className="col-span-2 rounded-lg border p-3">
                  <div className="mb-2 text-sm font-medium text-muted-foreground">
                    标题模板参考
                  </div>
                  <ul className="space-y-1 text-sm">
                    {recData.title_templates.map((t, i) => (
                      <li key={i}>· {typeof t === "string" ? t : JSON.stringify(t)}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
