"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  RefreshCw,
  TrendingUp,
  Clock,
  AlertCircle,
  CheckCircle,
  Plus,
  Trash2,
  BarChart3,
  Target,
  Activity,
  ChevronDown,
  ChevronUp,
  Eye,
  ThumbsUp,
  MessageSquare,
  Share2,
  Search,
  Bot,
} from "lucide-react";
import { toast } from "@/components/toaster";

/* ------------------------------------------------------------------ */
/* 类型定义                                                             */
/* ------------------------------------------------------------------ */

interface Competitor {
  id: string;
  user_id: string;
  platform: string;
  account_id: string;
  account_name: string;
  added_at: string;
  total_content: number;
  last_activity: string | null;
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
}

interface TopicItem {
  topic: string;
  count: number;
  ratio: number;
}

interface StyleItem {
  style: string;
  count: number;
  ratio: number;
}

interface TopContent {
  title: string;
  content_type: string;
  total_interaction: number;
  metrics: { views: number; likes: number; comments: number; shares: number };
  published_at: string;
  summary: string;
}

interface CompetitorAnalysis {
  topic_focus: TopicItem[];
  posting_frequency: string;
  avg_engagement: number;
  top_performing: TopContent[];
  style_analysis: StyleItem[];
  total_analyzed: number;
}

interface ComparisonData {
  competitor: {
    name: string;
    platform: string;
    total_content: number;
    avg_engagement: number;
    top_topics: string[];
  };
  user: {
    total_content: number;
    avg_engagement: number;
  };
  comparison: {
    engagement_gap: number;
    content_gap: number;
  };
}

/* ------------------------------------------------------------------ */
/* 平台颜色映射                                                         */
/* ------------------------------------------------------------------ */

const PLATFORM_COLORS: Record<string, string> = {
  "抖音": "bg-black text-white",
  "小红书": "bg-red-500 text-white",
  "B站": "bg-pink-500 text-white",
  "微博": "bg-orange-500 text-white",
  "知乎": "bg-blue-500 text-white",
  "头条": "bg-red-600 text-white",
  "公众号": "bg-green-600 text-white",
  "YouTube": "bg-red-700 text-white",
  "TikTok": "bg-gray-900 text-white",
  "快手": "bg-purple-600 text-white",
  "视频号": "bg-emerald-500 text-white",
  "百度热搜": "bg-rose-500 text-white",
  "Instagram": "bg-gradient-to-r from-yellow-500 via-pink-500 to-purple-600 text-white",
};

const PLATFORMS = ["抖音", "小红书", "B站", "微博", "知乎", "头条", "公众号", "YouTube", "TikTok", "快手", "视频号", "百度热搜", "Instagram"];

/* ------------------------------------------------------------------ */
/* 主组件                                                               */
/* ------------------------------------------------------------------ */

export default function MonitorPage() {
  /* 状态 */
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(false);

  // 添加表单
  const [showAddForm, setShowAddForm] = useState(false);
  const [newPlatform, setNewPlatform] = useState("抖音");
  const [newAccountId, setNewAccountId] = useState("");
  const [newAccountName, setNewAccountName] = useState("");

  // 展开详情
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<Record<string, CompetitorAnalysis>>({});
  const [analysisLoading, setAnalysisLoading] = useState<Record<string, boolean>>({});

  // 对比视图
  const [compareId, setCompareId] = useState<string | null>(null);
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);

  // 自动爬取
  const [scraping, setScraping] = useState(false);

  const user_id = "default";

  /* 获取竞品列表 */
  const fetchCompetitors = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/competitors?user_id=${user_id}`);
      const data = await res.json();
      setCompetitors(data.competitors || []);
    } catch {
      toast("获取竞品列表失败", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompetitors();
  }, []);

  /* 添加竞品 */
  const addCompetitor = async () => {
    if (!newAccountId.trim() || !newAccountName.trim()) {
      toast("请填写账号 ID 和名称", "error");
      return;
    }
    try {
      const res = await fetch("/api/competitors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id,
          platform: newPlatform,
          account_id: newAccountId.trim(),
          account_name: newAccountName.trim(),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        toast(data.error || "添加失败", "error");
        return;
      }
      toast("竞品添加成功", "success");
      setShowAddForm(false);
      setNewAccountId("");
      setNewAccountName("");
      fetchCompetitors();
    } catch {
      toast("添加竞品失败", "error");
    }
  };

  /* 删除竞品 */
  const removeCompetitor = async (id: string, name: string) => {
    if (!confirm(`确定移除 ${name} 吗？`)) return;
    try {
      const res = await fetch(`/api/competitors/${id}`, { method: "DELETE" });
      if (!res.ok) {
        toast("移除失败", "error");
        return;
      }
      toast("竞品已移除", "success");
      setCompetitors((prev) => prev.filter((c) => c.id !== id));
      if (expandedId === id) setExpandedId(null);
      if (compareId === id) setCompareId(null);
    } catch {
      toast("移除竞品失败", "error");
    }
  };

  /* 展开/收起分析 */
  const toggleExpand = async (id: string) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);

    if (!analysis[id]) {
      setAnalysisLoading((prev) => ({ ...prev, [id]: true }));
      try {
        const res = await fetch(`/api/competitors/${id}?action=analyze`);
        const data = await res.json();
        setAnalysis((prev) => ({ ...prev, [id]: data }));
      } catch {
        toast("获取分析数据失败", "error");
      } finally {
        setAnalysisLoading((prev) => ({ ...prev, [id]: false }));
      }
    }
  };

  /* 自动爬取所有竞品内容 */
  const scrapeAll = async () => {
    setScraping(true);
    toast("正在自动爬取竞品最新内容，请稍候...", "info");
    try {
      let successCount = 0;
      let failCount = 0;
      for (const comp of competitors) {
        try {
          const res = await fetch("/api/competitors/scrape", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_id,
              competitor_id: comp.id,
              platform: comp.platform,
              account_id: comp.account_id,
            }),
          });
          if (res.ok) successCount++;
          else failCount++;
        } catch {
          failCount++;
        }
      }
      if (successCount > 0 || failCount === 0) {
        toast(`自动爬取完成：成功 ${successCount} 个，失败 ${failCount} 个`, "success");
      } else {
        toast(`全部爬取失败（${failCount} 个），请检查后端爬虫服务`, "error");
      }
      // 刷新列表以获取最新数据
      fetchCompetitors();
    } catch {
      toast("爬取任务异常", "error");
    } finally {
      setScraping(false);
    }
  };
  const loadComparison = async (id: string) => {
    setCompareId(id);
    setComparisonLoading(true);
    setComparison(null);
    try {
      const res = await fetch(`/api/competitors/${id}?action=compare&user_id=${user_id}`);
      const data = await res.json();
      setComparison(data);
    } catch {
      toast("获取对比数据失败", "error");
    } finally {
      setComparisonLoading(false);
    }
  };

  /* 工具函数 */
  const formatNumber = (n: number): string => {
    if (n >= 10000) return (n / 10000).toFixed(1) + "w";
    if (n >= 1000) return (n / 1000).toFixed(1) + "k";
    return n.toString();
  };

  const formatDate = (iso: string | null): string => {
    if (!iso) return "未知";
    const d = new Date(iso);
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
  };

  /* ---------------------------------------------------------------- */
  /* 渲染                                                                */
  /* ---------------------------------------------------------------- */

  return (
    <div className="container py-8 space-y-8">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">竞品内容监控</h2>
          <p className="text-muted-foreground">追踪对标账号的内容策略和表现</p>
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={fetchCompetitors} disabled={loading} variant="outline">
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            刷新
          </Button>
          <Button
            onClick={scrapeAll}
            disabled={scraping || competitors.length === 0}
            variant="outline"
            className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
          >
            <Bot className={`mr-2 h-4 w-4 ${scraping ? "animate-spin" : ""}`} />
            {scraping ? "爬取中..." : "自动爬取"}
          </Button>
          <Button onClick={() => setShowAddForm(!showAddForm)}>
            <Plus className="mr-2 h-4 w-4" />
            添加竞品
          </Button>
        </div>
      </div>

      {/* 添加表单 */}
      {showAddForm && (
        <Card className="border-orange-500/30 bg-gradient-to-br from-orange-500/5 to-transparent">
          <CardHeader>
            <CardTitle className="text-lg">添加竞品账号</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <label className="mb-1 block text-sm font-medium">平台</label>
                <select
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
                  value={newPlatform}
                  onChange={(e) => setNewPlatform(e.target.value)}
                >
                  {PLATFORMS.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">账号 ID</label>
                <Input
                  placeholder="抖音号 / 小红书号 / 频道 ID..."
                  value={newAccountId}
                  onChange={(e) => setNewAccountId(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">账号名称</label>
                <Input
                  placeholder="竞品账号名称"
                  value={newAccountName}
                  onChange={(e) => setNewAccountName(e.target.value)}
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setShowAddForm(false)}>取消</Button>
              <Button onClick={addCompetitor}>确认添加</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 空状态 */}
      {!loading && competitors.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Search className="mb-4 h-12 w-12 text-muted-foreground/40" />
            <p className="text-lg font-medium text-muted-foreground">尚未添加竞品账号</p>
            <p className="mt-1 text-sm text-muted-foreground/60">添加竞品以追踪其内容策略</p>
            <Button className="mt-4" onClick={() => setShowAddForm(true)}>
              <Plus className="mr-2 h-4 w-4" />添加竞品
            </Button>
          </CardContent>
        </Card>
      )}

      {/* 竞品卡片网格 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {competitors.map((comp) => (
          <Card
            key={comp.id}
            className={`relative overflow-hidden transition-all duration-200 ${
              expandedId === comp.id ? "ring-2 ring-orange-500 shadow-lg" : "hover:shadow-md"
            }`}
          >
            {/* 玻璃拟态背景 */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-white/0 pointer-events-none" />

            <CardHeader className="pb-2">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <Badge className={PLATFORM_COLORS[comp.platform] || "bg-gray-500"}>
                    {comp.platform}
                  </Badge>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => loadComparison(comp.id)}
                    title="对比分析"
                  >
                    <BarChart3 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-red-500 hover:text-red-600"
                    onClick={() => removeCompetitor(comp.id, comp.account_name)}
                    title="移除"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <CardTitle className="text-base mt-1">{comp.account_name}</CardTitle>
              <CardDescription className="text-xs">ID: {comp.account_id}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-3">
              {/* 概览指标 */}
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="rounded-md bg-secondary/50 p-1.5">
                  <div className="font-bold text-base">{comp.total_content}</div>
                  <div className="text-muted-foreground">内容数</div>
                </div>
                <div className="rounded-md bg-secondary/50 p-1.5">
                  <div className="font-bold text-base text-blue-500">{formatNumber(comp.total_views)}</div>
                  <div className="text-muted-foreground">播放</div>
                </div>
                <div className="rounded-md bg-secondary/50 p-1.5">
                  <div className="font-bold text-base text-pink-500">{formatNumber(comp.total_likes)}</div>
                  <div className="text-muted-foreground">点赞</div>
                </div>
                <div className="rounded-md bg-secondary/50 p-1.5">
                  <div className="font-bold text-base text-green-500">{comp.total_comments}</div>
                  <div className="text-muted-foreground">评论</div>
                </div>
              </div>

              {/* 最近活跃 & 展开按钮 */}
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {comp.last_activity ? formatDate(comp.last_activity) : "暂无数据"}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => toggleExpand(comp.id)}
                >
                  {expandedId === comp.id ? (
                    <><ChevronUp className="mr-1 h-3 w-3" />收起</>
                  ) : (
                    <><ChevronDown className="mr-1 h-3 w-3" />分析</>
                  )}
                </Button>
              </div>

              {/* 展开分析视图 */}
              {expandedId === comp.id && (
                <div className="mt-3 space-y-4 border-t pt-4">
                  {analysisLoading[comp.id] ? (
                    <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      分析中...
                    </div>
                  ) : analysis[comp.id] ? (
                    <>
                      {/* 发布频率 & 互动率 */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="rounded-lg bg-gradient-to-br from-orange-500/10 to-transparent p-3">
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" /> 发布频率
                          </div>
                          <div className="mt-1 text-sm font-medium">
                            {analysis[comp.id].posting_frequency}
                          </div>
                        </div>
                        <div className="rounded-lg bg-gradient-to-br from-pink-500/10 to-transparent p-3">
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Activity className="h-3 w-3" /> 平均互动率
                          </div>
                          <div className="mt-1 text-sm font-medium">
                            {analysis[comp.id].avg_engagement}%
                          </div>
                        </div>
                      </div>

                      {/* 主题聚焦 */}
                      {analysis[comp.id].topic_focus.length > 0 && (
                        <div>
                          <h4 className="flex items-center gap-1 text-xs font-medium mb-2">
                            <Target className="h-3 w-3 text-orange-500" />
                            主题聚焦 TOP 5
                          </h4>
                          <div className="space-y-1.5">
                            {analysis[comp.id].topic_focus.slice(0, 5).map((t, i) => (
                              <div key={i} className="flex items-center gap-2 text-xs">
                                <span className="w-16 truncate">{t.topic}</span>
                                <div className="flex-1 h-1.5 bg-secondary rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-orange-500 rounded-full"
                                    style={{ width: `${t.ratio}%` }}
                                  />
                                </div>
                                <span className="w-10 text-right text-muted-foreground">{t.ratio}%</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 风格分析 */}
                      {analysis[comp.id].style_analysis.length > 0 && (
                        <div>
                          <h4 className="flex items-center gap-1 text-xs font-medium mb-2">
                            <TrendingUp className="h-3 w-3 text-blue-500" />
                            内容风格分布
                          </h4>
                          <div className="flex flex-wrap gap-1.5">
                            {analysis[comp.id].style_analysis.slice(0, 6).map((s, i) => (
                              <Badge key={i} variant="outline" className="text-xs">
                                {s.style} {s.ratio}%
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 最佳表现内容 */}
                      {analysis[comp.id].top_performing.length > 0 && (
                        <div>
                          <h4 className="flex items-center gap-1 text-xs font-medium mb-2">
                            <BarChart3 className="h-3 w-3 text-green-500" />
                            最佳表现内容
                          </h4>
                          <div className="space-y-2">
                            {analysis[comp.id].top_performing.slice(0, 3).map((item, i) => (
                              <div key={i} className="rounded-md bg-secondary/30 p-2 text-xs">
                                <div className="flex items-center justify-between">
                                  <span className="font-medium truncate flex-1">{item.title}</span>
                                  <Badge variant="secondary" className="ml-2 text-[10px] shrink-0">
                                    {item.content_type}
                                  </Badge>
                                </div>
                                <div className="mt-1 flex items-center gap-3 text-muted-foreground">
                                  <span className="flex items-center gap-0.5">
                                    <Eye className="h-3 w-3" />{formatNumber(item.metrics.views)}
                                  </span>
                                  <span className="flex items-center gap-0.5">
                                    <ThumbsUp className="h-3 w-3" />{formatNumber(item.metrics.likes)}
                                  </span>
                                  <span className="flex items-center gap-0.5">
                                    <MessageSquare className="h-3 w-3" />{item.metrics.comments}
                                  </span>
                                  <span className="flex items-center gap-0.5">
                                    <Share2 className="h-3 w-3" />{item.metrics.shares}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  ) : null}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 对比视图 */}
      {compareId && (
        <Card className="border-blue-500/30 bg-gradient-to-br from-blue-500/5 to-transparent">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-500" />
                竞品对比分析
              </CardTitle>
              <CardDescription>您与竞品的表现差异</CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setCompareId(null)}>
              关闭对比
            </Button>
          </CardHeader>
          <CardContent>
            {comparisonLoading ? (
              <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                加载对比数据...
              </div>
            ) : comparison ? (
              <div className="grid gap-6 md:grid-cols-2">
                {/* 竞品侧 */}
                <Card>
                  <CardHeader className="pb-2">
                    <Badge className={PLATFORM_COLORS[comparison.competitor.platform] || "bg-gray-500"}>
                      {comparison.competitor.platform}
                    </Badge>
                    <CardTitle className="text-base mt-1">{comparison.competitor.name}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">内容总数</span>
                      <span className="font-medium">{comparison.competitor.total_content}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">互动率</span>
                      <span className="font-medium text-orange-500">{comparison.competitor.avg_engagement}%</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground text-xs">核心主题</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {comparison.competitor.top_topics.map((t, i) => (
                          <Badge key={i} variant="secondary" className="text-[10px]">{t}</Badge>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* 用户侧 */}
                <Card>
                  <CardHeader className="pb-2">
                    <Badge className="bg-purple-500 text-white">你</Badge>
                    <CardTitle className="text-base mt-1">我的内容</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">内容总数</span>
                      <span className="font-medium">{comparison.user.total_content}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">互动率</span>
                      <span className="font-medium text-blue-500">{comparison.user.avg_engagement}%</span>
                    </div>
                  </CardContent>
                </Card>

                {/* 差距总结 */}
                <Card className="md:col-span-2 border-yellow-500/30">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Activity className="h-4 w-4 text-yellow-500" />
                      差距总结
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="rounded-lg bg-secondary/50 p-3">
                        <div className="text-xs text-muted-foreground">互动率差距</div>
                        <div className={`text-lg font-bold ${
                          comparison.comparison.engagement_gap > 0 ? "text-orange-500" : "text-green-500"
                        }`}>
                          {comparison.comparison.engagement_gap > 0 ? "+" : ""}
                          {comparison.comparison.engagement_gap}%
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {comparison.comparison.engagement_gap > 0
                            ? "竞品互动率更高，值得学习"
                            : "您的互动率领先竞品"}
                        </div>
                      </div>
                      <div className="rounded-lg bg-secondary/50 p-3">
                        <div className="text-xs text-muted-foreground">内容数量差距</div>
                        <div className={`text-lg font-bold ${
                          comparison.comparison.content_gap > 0 ? "text-orange-500" : "text-green-500"
                        }`}>
                          {comparison.comparison.content_gap > 0 ? "+" : ""}
                          {comparison.comparison.content_gap}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {comparison.comparison.content_gap > 0
                            ? "竞品发布更频繁"
                            : "您的内容数量领先"}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}

      {/* 竞品数量提示 */}
      {competitors.length > 0 && (
        <p className="text-center text-xs text-muted-foreground">
          共追踪 {competitors.length} 个竞品账号
        </p>
      )}
    </div>
  );
}
