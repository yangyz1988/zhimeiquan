"use client";

import { useState, useEffect } from "react";
import { ModelRouterPanel } from "@/components/model-router-panel";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Brain, Zap, DollarSign, Clock, Loader2, AlertCircle, Trophy,
  BarChart3, TrendingUp, Cpu, Sparkles, ArrowRight,
  CheckCircle2, ChevronRight, Target, Gauge,
} from "lucide-react";
import { toast } from "@/components/toaster";

interface ModelProfile {
  name: string;
  cost_per_1k: number;
  avg_latency_ms: number;
  quality: number;
  best_for: string[];
}

interface CostEstimate {
  promptTokens: number;
  completionTokens: number;
  modelName: string;
  costPer1k: number;
  estimatedCost: number;
}

const CAPABILITY_LABELS: Record<string, string> = {
  content_generation: "内容生成",
  title_generation: "标题生成",
  scoring: "内容评分",
  analysis: "深度分析",
  creative: "创意写作",
  translation: "翻译",
  chat: "对话交流",
};

const CAPABILITY_MAP: Record<string, string[]> = {
  "GPT-4o": ["content_generation", "creative", "analysis", "translation", "chat"],
  "Claude 3.5 Sonnet": ["content_generation", "creative", "analysis", "chat", "scoring"],
  "DeepSeek V3": ["content_generation", "title_generation", "chat", "translation"],
  "Qwen 2.5": ["content_generation", "title_generation", "chat"],
  "Yi-Large": ["content_generation", "creative", "analysis"],
};

export default function RouterPage() {
  const [profiles, setProfiles] = useState<Record<string, ModelProfile>>({});
  const [profilesLoading, setProfilesLoading] = useState(true);
  const [profilesError, setProfilesError] = useState(false);

  // Cost estimator state
  const [estimatePrompt, setEstimatePrompt] = useState("");
  const [estimateModel, setEstimateModel] = useState("");
  const [costResult, setCostResult] = useState<CostEstimate | null>(null);
  const [estimating, setEstimating] = useState(false);

  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = async () => {
    setProfilesLoading(true);
    setProfilesError(false);
    try {
      const res = await fetch("/api/v1/router/profiles");
      if (!res.ok) throw new Error("Failed to load");
      const data = await res.json();
      setProfiles(data);
      const keys = Object.keys(data);
      if (keys.length > 0) setEstimateModel(keys[0]);
    } catch (error) {
      console.error(error);
      setProfilesError(true);
      toast("加载模型列表失败", "error");
    } finally {
      setProfilesLoading(false);
    }
  };

  const estimateCost = () => {
    if (!estimatePrompt.trim()) {
      toast("请输入提示词以估算成本", "warning");
      return;
    }
    if (!estimateModel || !profiles[estimateModel]) {
      toast("请选择模型", "warning");
      return;
    }

    setEstimating(true);
    // Simulate token counting (rough estimate: ~2 chars per token for Chinese)
    const charCount = estimatePrompt.length;
    const estimatedPromptTokens = Math.ceil(charCount / 2);
    const estimatedCompletionTokens = Math.ceil(estimatedPromptTokens * 0.6);
    const model = profiles[estimateModel];
    const cost = ((estimatedPromptTokens + estimatedCompletionTokens) / 1000) * model.cost_per_1k;

    setTimeout(() => {
      setCostResult({
        promptTokens: estimatedPromptTokens,
        completionTokens: estimatedCompletionTokens,
        modelName: model.name,
        costPer1k: model.cost_per_1k,
        estimatedCost: Math.round(cost * 10000) / 10000,
      });
      setEstimating(false);
    }, 600);
  };

  // Model comparison data
  const modelEntries = Object.entries(profiles);
  const bestQuality = modelEntries.length > 0
    ? modelEntries.reduce((best, [, p]) => p.quality > best.quality ? p : best, modelEntries[0][1])
    : null;
  const fastestModel = modelEntries.length > 0
    ? modelEntries.reduce((best, [, p]) => p.avg_latency_ms < best.avg_latency_ms ? p : best, modelEntries[0][1])
    : null;
  const cheapestModel = modelEntries.length > 0
    ? modelEntries.reduce((best, [, p]) => p.cost_per_1k < best.cost_per_1k ? p : best, modelEntries[0][1])
    : null;

  const qualityBar = (q: number): string => {
    if (q >= 1.0) return "bg-green-500";
    if (q >= 0.8) return "bg-green-400";
    if (q >= 0.6) return "bg-yellow-400";
    return "bg-red-400";
  };

  return (
    <div className="container py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="flex items-center gap-2 text-3xl font-bold">
          <Brain className="h-7 w-7 text-orange-400" />
          智能模型路由
        </h1>
        <p className="mt-1 text-muted-foreground">
          根据任务类型和优化目标，自动选择最优 AI 模型处理你的请求
        </p>
      </div>

      {/* Model Comparison Cards */}
      {profilesLoading ? (
        <div className="grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="glass-card h-40 animate-pulse rounded-xl border-white/5 p-4">
              <div className="mb-3 h-4 w-1/2 rounded bg-white/10" />
              <div className="mb-2 h-3 w-3/4 rounded bg-white/10" />
              <div className="h-3 w-1/2 rounded bg-white/10" />
            </div>
          ))}
        </div>
      ) : profilesError ? (
        <Card className="border-red-500/20 bg-red-500/5">
          <CardContent className="flex flex-col items-center gap-3 py-6">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <p className="text-sm text-white/60">模型列表加载失败</p>
            <Button variant="outline" size="sm" onClick={fetchProfiles} className="border-white/10">
              重试
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Quick comparison top picks */}
          <div className="grid gap-4 md:grid-cols-3">
            {/* Best Quality */}
            {bestQuality && (
              <Card className="border-green-500/20 bg-gradient-to-br from-green-500/5 to-transparent">
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-500/10">
                      <Trophy className="h-4 w-4 text-green-400" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white/70">{bestQuality.name}</div>
                      <div className="text-xs text-green-400">最高质量</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-white/40">质量评分</span>
                      <span className="text-green-400 font-semibold">{(bestQuality.quality * 100).toFixed(0)}</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
                      <div className="h-full rounded-full bg-gradient-to-r from-green-500 to-emerald-400" style={{ width: `${bestQuality.quality * 100}%` }} />
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-white/40">延迟</span>
                      <span className="text-white/50">{bestQuality.avg_latency_ms}ms</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-white/40">成本</span>
                      <span className="text-white/50">¥{bestQuality.cost_per_1k}/1k tokens</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Fastest */}
            {fastestModel && (
              <Card className="border-blue-500/20 bg-gradient-to-br from-blue-500/5 to-transparent">
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10">
                      <Gauge className="h-4 w-4 text-blue-400" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white/70">{fastestModel.name}</div>
                      <div className="text-xs text-blue-400">最快速度</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-white/40">延迟</span>
                      <span className="text-blue-400 font-semibold">{fastestModel.avg_latency_ms}ms</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
                      <div className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400" style={{ width: `${Math.max(10, 100 - (fastestModel.avg_latency_ms / 20))}%` }} />
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-white/40">质量评分</span>
                      <span className="text-white/50">{(fastestModel.quality * 100).toFixed(0)}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-white/40">成本</span>
                      <span className="text-white/50">¥{fastestModel.cost_per_1k}/1k tokens</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Cheapest */}
            {cheapestModel && (
              <Card className="border-purple-500/20 bg-gradient-to-br from-purple-500/5 to-transparent">
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10">
                      <DollarSign className="h-4 w-4 text-purple-400" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white/70">{cheapestModel.name}</div>
                      <div className="text-xs text-purple-400">最低成本</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-white/40">成本</span>
                      <span className="text-purple-400 font-semibold">¥{cheapestModel.cost_per_1k}/1k tokens</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
                      <div className="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-400" style={{ width: `${Math.max(10, 100 - (cheapestModel.cost_per_1k * 10))}%` }} />
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-white/40">质量评分</span>
                      <span className="text-white/50">{(cheapestModel.quality * 100).toFixed(0)}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-white/40">延迟</span>
                      <span className="text-white/50">{cheapestModel.avg_latency_ms}ms</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Model Capability Comparison Table */}
          <Card className="border-white/5 bg-white/[0.02]">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Cpu className="h-5 w-5 text-orange-400" />
                模型能力对比
              </CardTitle>
              <CardDescription>各模型擅长的任务类型概览</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="px-3 py-2 text-left text-xs font-medium text-white/40">模型</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-white/40">质量</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-white/40">延迟</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-white/40">成本</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-white/40">擅长任务</th>
                    </tr>
                  </thead>
                  <tbody>
                    {modelEntries.map(([key, p]) => {
                      const capabilities = CAPABILITY_MAP[p.name] || p.best_for || [];
                      return (
                        <tr key={key} className="border-b border-white/5 transition-colors hover:bg-white/[0.02]">
                          <td className="px-3 py-3">
                            <span className="font-medium text-white/70">{p.name}</span>
                            <div className="text-[10px] text-white/30">{key}</div>
                          </td>
                          <td className="px-3 py-3">
                            <div className="flex items-center gap-2">
                              <div className="h-1.5 flex-1 rounded-full bg-white/5">
                                <div
                                  className={`h-full rounded-full ${qualityBar(p.quality)}`}
                                  style={{ width: `${p.quality * 100}%` }}
                                />
                              </div>
                              <span className="text-xs text-white/50">{(p.quality * 100).toFixed(0)}</span>
                            </div>
                          </td>
                          <td className="px-3 py-3">
                            <span className="text-white/50">{p.avg_latency_ms}ms</span>
                          </td>
                          <td className="px-3 py-3">
                            <span className="text-white/50">¥{p.cost_per_1k}</span>
                          </td>
                          <td className="px-3 py-3">
                            <div className="flex flex-wrap gap-1">
                              {capabilities.slice(0, 3).map((cap) => (
                                <Badge key={cap} variant="outline" className="border-white/10 text-[10px] text-white/40">
                                  {CAPABILITY_LABELS[cap] || cap}
                                </Badge>
                              ))}
                              {capabilities.length > 3 && (
                                <Badge variant="outline" className="border-white/10 text-[10px] text-white/30">
                                  +{capabilities.length - 3}
                                </Badge>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Cost Estimator */}
      {modelEntries.length > 0 && (
        <Card className="border-white/5 bg-gradient-to-br from-orange-500/5 to-transparent">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <DollarSign className="h-5 w-5 text-orange-400" />
              成本预估
            </CardTitle>
            <CardDescription>输入提示词，预估各模型的 token 消耗与费用</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-3">
              <div className="flex-1">
                <Input
                  placeholder="输入你的提示词..."
                  value={estimatePrompt}
                  onChange={(e) => setEstimatePrompt(e.target.value)}
                  className="border-white/10 bg-white/5 text-white placeholder:text-white/20"
                />
                <p className="mt-1 text-xs text-white/30">
                  约 {estimatePrompt.length} 字符 · 预估 {Math.ceil(estimatePrompt.length / 2)} tokens
                </p>
              </div>
              <Button
                onClick={estimateCost}
                disabled={estimating}
                className="bg-gradient-to-r from-orange-500 to-pink-500 text-white shrink-0"
              >
                {estimating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <Sparkles className="mr-1.5 h-4 w-4" />
                    估算
                  </>
                )}
              </Button>
            </div>

            {costResult && (
              <div className="rounded-xl border border-orange-500/20 bg-black/20 p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-400" />
                    <span className="text-sm font-medium text-white/70">
                      使用 {costResult.modelName}
                    </span>
                  </div>
                  <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/30">
                    预估费用
                  </Badge>
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-lg border border-white/5 p-3 text-center">
                    <div className="text-lg font-bold text-white/80">{costResult.promptTokens.toLocaleString()}</div>
                    <div className="text-xs text-white/40">输入 tokens</div>
                  </div>
                  <div className="rounded-lg border border-white/5 p-3 text-center">
                    <div className="text-lg font-bold text-white/80">{costResult.completionTokens.toLocaleString()}</div>
                    <div className="text-xs text-white/40">输出 tokens</div>
                  </div>
                  <div className="rounded-lg border border-orange-500/20 bg-orange-500/5 p-3 text-center">
                    <div className="text-lg font-bold text-orange-400">¥{costResult.estimatedCost.toFixed(4)}</div>
                    <div className="text-xs text-white/40">预估费用 (¥{costResult.costPer1k}/1k tokens)</div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Existing Model Router Panel */}
      <ModelRouterPanel />
    </div>
  );
}
