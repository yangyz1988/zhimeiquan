"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Brain, Zap, DollarSign, Clock, Loader2 } from "lucide-react";
import { toast } from "@/components/toaster";

interface ModelInfo {
  name: string;
  cost_per_1k: number;
  avg_latency_ms: number;
  quality: number;
  best_for: string[];
}

export function ModelRouterPanel() {
  const [profiles, setProfiles] = useState<Record<string, ModelInfo>>({});
  const [recommendation, setRecommendation] = useState<string>("");
  const [taskType, setTaskType] = useState("content_generation");
  const [priority, setPriority] = useState("balanced");
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<{ result: string; model: string; duration_ms: number } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch("/api/v1/router/profiles")
      .then((r) => r.json())
      .then(setProfiles)
      .catch(console.error);
  }, []);

  const recommend = async () => {
    const res = await fetch(
      `/api/v1/router/recommend?task_type=${taskType}&priority=${priority}`
    );
    const data = await res.json();
    setRecommendation(data.recommended);
  };

  const execute = async () => {
    if (!prompt.trim()) {
      toast("请输入提示词", "error");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/v1/router/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, task_type: taskType, priority }),
      });
      const data = await res.json();
      setResult(data);
      toast(`已用 ${data.model_name} 完成`, "success");
    } catch (e) {
      toast("执行失败", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="flex items-center gap-2 text-3xl font-bold">
          <Brain className="h-7 w-7 text-orange-500" />
          智能模型路由
        </h1>
        <p className="text-muted-foreground">根据任务自动选择最优模型</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>模型库</CardTitle>
            <CardDescription>所有可用 AI 模型</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(profiles).map(([key, p]) => (
              <div key={key} className="rounded-lg border p-3">
                <div className="mb-2 flex items-center justify-between">
                  <div>
                    <div className="font-medium">{p.name}</div>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {p.best_for.map((t) => (
                        <Badge key={t} variant="secondary" className="text-xs">
                          {t}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="flex items-center gap-1">
                    <DollarSign className="h-3 w-3" />
                    <span>¥{p.cost_per_1k}/1k</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    <span>{p.avg_latency_ms}ms</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Zap className="h-3 w-3" />
                    <span>{(p.quality * 100).toFixed(0)}分</span>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>智能推荐</CardTitle>
            <CardDescription>选择任务类型和优先级</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">任务类型</label>
              <select
                value={taskType}
                onChange={(e) => setTaskType(e.target.value)}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              >
                <option value="content_generation">内容生成</option>
                <option value="title_generation">标题生成</option>
                <option value="scoring">评分</option>
                <option value="analysis">深度分析</option>
                <option value="creative">创意写作</option>
                <option value="translation">翻译</option>
                <option value="chat">对话</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">优化目标</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              >
                <option value="cost">最低成本</option>
                <option value="speed">最快速度</option>
                <option value="quality">最高质量</option>
                <option value="balanced">均衡</option>
              </select>
            </div>
            <Button onClick={recommend} className="w-full">
              推荐模型
            </Button>
            {recommendation && (
              <div className="rounded-md border bg-orange-50 p-3 text-center dark:bg-orange-950/20">
                <div className="text-sm text-muted-foreground">推荐使用</div>
                <div className="text-lg font-bold text-orange-600">
                  {profiles[recommendation]?.name || recommendation}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>在线测试</CardTitle>
          <CardDescription>体验智能路由效果</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="输入提示词..."
            className="min-h-[100px] w-full rounded-md border bg-background p-3 text-sm"
          />
          <Button onClick={execute} disabled={loading} className="w-full">
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                路由中...
              </>
            ) : (
              <>
                <Brain className="mr-2 h-4 w-4" />
                执行
              </>
            )}
          </Button>
          {result && (
            <div className="rounded-md border bg-muted/30 p-3">
              <div className="mb-2 flex items-center justify-between text-sm">
                <Badge>{result.model}</Badge>
                <span className="text-muted-foreground">{result.duration_ms}ms</span>
              </div>
              <p className="whitespace-pre-wrap text-sm">{result.result}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
