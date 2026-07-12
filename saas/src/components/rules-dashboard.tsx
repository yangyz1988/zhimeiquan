"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RefreshCw, TrendingUp, Clock, AlertCircle, CheckCircle, Target, Activity, BarChart3, Eye, ThumbsUp, MessageSquare, Share2, ChevronDown, ChevronUp } from "lucide-react";
import { toast } from "@/components/toaster";

interface Rule {
  rule: string;
  example?: string;
  importance?: string;
  reason?: string;
}

interface HookPattern {
  pattern: string;
  description: string;
  examples: string[];
}

interface PlatformRules {
  title_rules?: Rule[];
  content_rules?: Rule[];
  hook_patterns?: HookPattern[];
  trending_topics?: string[];
  best_practices?: string[];
  avoid_list?: string[];
  score?: { hook: number; trend: number; engagement: number; monetization: number };
  title_analysis?: {
    total: number;
    patterns: Record<string, number>;
    hot_keywords: string[];
    examples: Record<string, string[]>;
  };
}

interface RulesData {
  updated_at: string | null;
  platforms: string[];
  rules: Record<string, PlatformRules>;
}

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
};

export function RulesDashboard() {
  const [data, setData] = useState<RulesData | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [status, setStatus] = useState<{ expired: boolean; age_hours: number | null } | null>(null);

  const fetchRules = async () => {
    setLoading(true);
    try {
      const [rulesRes, statusRes] = await Promise.all([
        fetch("/api/monitor/rules"),
        fetch("/api/monitor/rules/status"),
      ]);
      const rulesData = await rulesRes.json();
      const statusData = await statusRes.json();
      setData(rulesData);
      setStatus(statusData);
    } catch (error) {
      console.error("获取规则失败:", error);
      toast("获取规则失败", "error");
    } finally {
      setLoading(false);
    }
  };

  const refreshRules = async () => {
    setLoading(true);
    try {
      await fetch("/api/monitor/rules/refresh", { method: "POST" });
      await fetchRules();
    } catch (error) {
      console.error("刷新失败:", error);
      toast("刷新失败，请稍后重试", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const selectedRules = selectedPlatform ? data?.rules[selectedPlatform] : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">爆款规则监控</h2>
          <p className="text-muted-foreground">实时追踪各平台算法和爆款规律</p>
        </div>
        <div className="flex items-center gap-4">
          {status && (
            <div className="flex items-center gap-2 text-sm">
              {status.expired ? (
                <>
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                  <span className="text-yellow-600">规则已过期</span>
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-muted-foreground">
                    更新于 {status.age_hours?.toFixed(1)} 小时前
                  </span>
                </>
              )}
            </div>
          )}
          <Button onClick={refreshRules} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            刷新规则
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {data?.platforms.map((platform) => {
          const rules = data.rules[platform];
          const score = rules?.score;
          return (
            <Card
              key={platform}
              className={`cursor-pointer transition-all hover:shadow-lg ${
                selectedPlatform === platform ? "ring-2 ring-orange-500" : ""
              }`}
              onClick={() => setSelectedPlatform(platform)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <Badge className={PLATFORM_COLORS[platform] || "bg-gray-500"}>
                    {platform}
                  </Badge>
                  {score && (
                    <span className="text-lg font-bold text-orange-500">
                      {Math.round((score.hook + score.trend + score.engagement + score.monetization) / 4)}
                    </span>
                  )}
                </div>
                <CardTitle className="text-sm">{rules?.title_rules?.length || 0} 条标题规则</CardTitle>
                <CardDescription>{rules?.content_rules?.length || 0} 条内容规则</CardDescription>
              </CardHeader>
              <CardContent>
                {score && (
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>钩子力: {score.hook}</div>
                    <div>趋势度: {score.trend}</div>
                    <div>互动率: {score.engagement}</div>
                    <div>变现力: {score.monetization}</div>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {selectedRules && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-orange-500" />
                标题规则 - {selectedPlatform}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {selectedRules.title_rules?.map((rule, i) => (
                <div key={i} className="border-l-2 border-orange-500 pl-3">
                  <p className="font-medium">{rule.rule}</p>
                  {rule.example && (
                    <p className="text-sm text-muted-foreground">例: {rule.example}</p>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>钩子模式</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {selectedRules.hook_patterns?.map((hook, i) => (
                <div key={i} className="rounded-lg bg-secondary p-3">
                  <p className="font-medium">{hook.pattern}</p>
                  <p className="text-sm text-muted-foreground">{hook.description}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {hook.examples.map((ex, j) => (
                      <Badge key={j} variant="outline" className="text-xs">
                        {ex}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {selectedRules.title_analysis && (
            <Card>
              <CardHeader>
                <CardTitle>热门关键词</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {selectedRules.title_analysis.hot_keywords.map((kw, i) => (
                    <Badge key={i} variant="secondary">
                      {kw}
                    </Badge>
                  ))}
                </div>
                <div className="mt-4">
                  <h4 className="mb-2 text-sm font-medium">标题模式分布</h4>
                  {Object.entries(selectedRules.title_analysis.patterns).map(([pattern, count]) => (
                    <div key={pattern} className="flex items-center gap-2 text-sm">
                      <span className="w-20">{pattern}</span>
                      <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-orange-500"
                          style={{ width: `${(count / (selectedRules.title_analysis!.total || 1)) * 100}%` }}
                        />
                      </div>
                      <span className="w-8 text-right">{count}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>最佳实践 & 避坑</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="mb-2 text-sm font-medium text-green-600">最佳实践</h4>
                <ul className="space-y-1">
                  {selectedRules.best_practices?.map((p, i) => (
                    <li key={i} className="text-sm">• {p}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="mb-2 text-sm font-medium text-red-600">避坑事项</h4>
                <ul className="space-y-1">
                  {selectedRules.avoid_list?.map((a, i) => (
                    <li key={i} className="text-sm">• {a}</li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 竞品分析洞察 */}
      <CompetitorInsights />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* 竞品分析洞察 - 内容主题 / 发布频率 / 互动基准                          */
/* ------------------------------------------------------------------ */

interface CompetitorSummary {
  id: string;
  account_name: string;
  platform: string;
  total_content: number;
  total_views: number;
  total_likes: number;
}

interface TopicInsight {
  topic: string;
  count: number;
  ratio: number;
}

interface StyleInsight {
  style: string;
  count: number;
  ratio: number;
}

function CompetitorInsights() {
  const [competitors, setCompetitors] = useState<CompetitorSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  // 汇集主题数据
  const [themeDistribution, setThemeDistribution] = useState<Record<string, number>>({});
  const [styleDistribution, setStyleDistribution] = useState<Record<string, number>>({});
  const [engagementBenchmark, setEngagementBenchmark] = useState(0);
  const [totalAnalyzed, setTotalAnalyzed] = useState(0);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      // 1. 获取竞品列表
      const listRes = await fetch("/api/competitors?user_id=default");
      const listData = await listRes.json();
      const comps: CompetitorSummary[] = (listData.competitors || []).map((c: any) => ({
        id: c.id,
        account_name: c.account_name,
        platform: c.platform,
        total_content: c.total_content || 0,
        total_views: c.total_views || 0,
        total_likes: c.total_likes || 0,
      }));
      setCompetitors(comps);

      // 2. 逐个分析并汇总
      const allTopics: Record<string, number> = {};
      const allStyles: Record<string, number> = {};
      let totalEngagement = 0;
      let analyzedCount = 0;

      for (const comp of comps) {
        try {
          const anaRes = await fetch(`/api/competitors/${comp.id}?action=analyze`);
          const analysis = await anaRes.json();
          if (analysis.topic_focus) {
            for (const t of analysis.topic_focus) {
              allTopics[t.topic] = (allTopics[t.topic] || 0) + t.count;
            }
          }
          if (analysis.style_analysis) {
            for (const s of analysis.style_analysis) {
              allStyles[s.style] = (allStyles[s.style] || 0) + s.count;
            }
          }
          if (analysis.avg_engagement) {
            totalEngagement += analysis.avg_engagement;
            analyzedCount++;
          }
        } catch {
          // 单个竞品分析失败不影响整体
        }
      }

      setThemeDistribution(allTopics);
      setStyleDistribution(allStyles);
      setEngagementBenchmark(analyzedCount > 0 ? Math.round(totalEngagement / analyzedCount * 100) / 100 : 0);
      setTotalAnalyzed(comps.length);
    } catch {
      // 静默处理
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  // 排序后的主题/风格
  const sortedThemes = Object.entries(themeDistribution)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10);
  const sortedStyles = Object.entries(styleDistribution)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 8);
  const maxThemeCount = Math.max(...sortedThemes.map(([, c]) => c), 1);

  if (totalAnalyzed === 0 && !loading) return null;

  return (
    <Card className="border-green-500/30">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-green-500" />
            竞品分析洞察
          </CardTitle>
          <CardDescription>
            基于 {totalAnalyzed} 个竞品账号的内容策略汇总
          </CardDescription>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => { setExpanded(!expanded); if (!expanded) fetchInsights(); }}
        >
          {loading ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : expanded ? (
            <><ChevronUp className="mr-1 h-4 w-4" />收起</>
          ) : (
            <><ChevronDown className="mr-1 h-4 w-4" />展开分析</>
          )}
        </Button>
      </CardHeader>

      {expanded && (
        <CardContent className="space-y-6">
          {/* 跟踪账号摘要 */}
          {competitors.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {competitors.map((c) => (
                <Badge key={c.id} variant="outline" className="text-xs">
                  {c.platform} · {c.account_name}
                  <span className="ml-1 text-muted-foreground">({c.total_content})</span>
                </Badge>
              ))}
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* 内容主题 TOP 10 */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-1">
                  <Target className="h-4 w-4 text-orange-500" />
                  热门内容主题
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {sortedThemes.map(([theme, count]) => (
                  <div key={theme} className="flex items-center gap-2 text-xs">
                    <span className="w-20 truncate">{theme}</span>
                    <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-orange-500 to-pink-500 rounded-full"
                        style={{ width: `${(count / maxThemeCount) * 100}%` }}
                      />
                    </div>
                    <span className="w-8 text-right text-muted-foreground">{count}</span>
                  </div>
                ))}
                {sortedThemes.length === 0 && (
                  <p className="text-xs text-muted-foreground">暂无主题数据</p>
                )}
              </CardContent>
            </Card>

            {/* 内容风格分布 */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-1">
                  <Activity className="h-4 w-4 text-blue-500" />
                  内容风格分布
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {sortedStyles.map(([style, count]) => (
                  <div key={style} className="flex items-center gap-2 text-xs">
                    <span className="w-16 truncate">{style}</span>
                    <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                        style={{ width: `${(count / maxThemeCount) * 100}%` }}
                      />
                    </div>
                    <span className="w-8 text-right text-muted-foreground">{count}</span>
                  </div>
                ))}
                {sortedStyles.length === 0 && (
                  <p className="text-xs text-muted-foreground">暂无风格数据</p>
                )}
              </CardContent>
            </Card>

            {/* 发布频率 & 互动基准 */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-1">
                  <BarChart3 className="h-4 w-4 text-green-500" />
                  互动基准
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="text-xs text-muted-foreground mb-1">竞品平均互动率</div>
                  <div className="text-2xl font-bold text-green-500">{engagementBenchmark}%</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-1">跟踪竞品数</div>
                  <div className="text-2xl font-bold">{totalAnalyzed}</div>
                </div>
                <div className="rounded-md bg-secondary/50 p-2 text-xs text-muted-foreground">
                  <p>互动基准 = 竞品平均互动率的汇总，可作为您内容策略的参考目标。</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
