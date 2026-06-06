"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, Users, Eye, Heart, MessageCircle, Share2, BarChart3, Activity } from "lucide-react";
import { Loading } from "@/components/loading";

interface PlatformStat {
  count: number;
  views: number;
  likes: number;
}

interface AnalyticsData {
  total_content: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  avg_engagement: number;
  content_list: Array<{
    title: string;
    platform: string;
    metrics: { views: number; likes: number; comments: number; shares: number };
  }>;
}

export function AnalyticsDashboard() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [platforms, setPlatforms] = useState<Record<string, PlatformStat>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // 模拟数据 - 实际从 API 获取
      const mockData: AnalyticsData = {
        total_content: 12,
        total_views: 156000,
        total_likes: 8200,
        total_comments: 1100,
        total_shares: 380,
        avg_engagement: 6.1,
        content_list: [
          { title: "AI时代普通人的机会", platform: "抖音", metrics: { views: 45000, likes: 2300, comments: 320, shares: 110 } },
          { title: "3个底层逻辑", platform: "小红书", metrics: { views: 32000, likes: 1800, comments: 250, shares: 90 } },
          { title: "自媒体赚钱真相", platform: "B站", metrics: { views: 28000, likes: 1500, comments: 180, shares: 70 } },
          { title: "AI工具推荐", platform: "公众号", metrics: { views: 18000, likes: 800, comments: 120, shares: 50 } },
          { title: "效率翻倍", platform: "抖音", metrics: { views: 33000, likes: 1800, comments: 230, shares: 60 } },
        ],
      };
      setData(mockData);
      
      const mockPlatforms: Record<string, PlatformStat> = {
        "抖音": { count: 5, views: 78000, likes: 4100 },
        "小红书": { count: 3, views: 32000, likes: 1800 },
        "B站": { count: 2, views: 28000, likes: 1500 },
        "公众号": { count: 2, views: 18000, likes: 800 },
      };
      setPlatforms(mockPlatforms);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <Loading message="加载分析数据中..." />;
  }

  if (!data) {
    return <div className="p-8 text-center text-muted-foreground">暂无数据</div>;
  }

  const stats = [
    { label: "总内容数", value: data.total_content, icon: BarChart3, color: "text-blue-500" },
    { label: "总曝光", value: data.total_views.toLocaleString(), icon: Eye, color: "text-purple-500" },
    { label: "总点赞", value: data.total_likes.toLocaleString(), icon: Heart, color: "text-red-500" },
    { label: "总评论", value: data.total_comments.toLocaleString(), icon: MessageCircle, color: "text-green-500" },
    { label: "总分享", value: data.total_shares.toLocaleString(), icon: Share2, color: "text-orange-500" },
    { label: "平均互动率", value: `${data.avg_engagement}%`, icon: TrendingUp, color: "text-pink-500" },
  ];

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold">数据仪表盘</h1>
        <p className="text-muted-foreground">实时追踪内容表现</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
        {stats.map((s) => (
          <Card key={s.label}>
            <CardContent className="p-4">
              <s.icon className={`mb-2 h-5 w-5 ${s.color}`} />
              <div className="text-2xl font-bold">{s.value}</div>
              <div className="text-xs text-muted-foreground">{s.label}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>平台分布</CardTitle>
            <CardDescription>各平台内容表现</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(platforms).map(([platform, stat]) => {
              const total = data.total_views;
              const pct = (stat.views / total) * 100;
              return (
                <div key={platform}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="font-medium">{platform}</span>
                    <span className="text-muted-foreground">
                      {stat.views.toLocaleString()} ({pct.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                    <div
                      className="h-full bg-gradient-to-r from-orange-500 to-pink-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="mt-1 flex gap-4 text-xs text-muted-foreground">
                    <span>{stat.count} 篇</span>
                    <span>{stat.likes.toLocaleString()} 赞</span>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>热门内容 TOP 5</CardTitle>
            <CardDescription>按曝光量排序</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.content_list
              .sort((a, b) => b.metrics.views - a.metrics.views)
              .slice(0, 5)
              .map((c, i) => (
                <div key={i} className="flex items-center justify-between rounded-lg border p-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-orange-500">#{i + 1}</span>
                      <span className="font-medium">{c.title}</span>
                    </div>
                    <div className="mt-1 flex gap-3 text-xs text-muted-foreground">
                      <Badge variant="outline">{c.platform}</Badge>
                      <span>👁 {c.metrics.views.toLocaleString()}</span>
                      <span>❤ {c.metrics.likes.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            <Activity className="mr-2 inline h-5 w-5" />
            趋势洞察
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-lg border-l-4 border-green-500 bg-green-50 p-3 dark:bg-green-950/20">
              <div className="text-sm font-medium text-green-700 dark:text-green-400">
                🚀 增长亮点
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                AI时代普通人机会 比上周增长 32%，建议加大该主题投入
              </p>
            </div>
            <div className="rounded-lg border-l-4 border-orange-500 bg-orange-50 p-3 dark:bg-orange-950/20">
              <div className="text-sm font-medium text-orange-700 dark:text-orange-400">
                ⚠️ 待优化
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                公众号内容互动率偏低，建议增加问题引导提升评论
              </p>
            </div>
            <div className="rounded-lg border-l-4 border-blue-500 bg-blue-50 p-3 dark:bg-blue-950/20">
              <div className="text-sm font-medium text-blue-700 dark:text-blue-400">
                💡 建议
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                抖音和小红书表现最佳，可拓展 2 倍发布频次
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
