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
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Plus, Trophy, BarChart3 } from "lucide-react";
import { toast } from "@/components/toaster";

interface Variant {
  id: string;
  title: string;
  content: string;
  metrics: { views: number; likes: number; comments: number; shares: number };
}

interface ABTest {
  test_id: string;
  project_id: string;
  variants: Variant[];
  status: string;
  created_at: string;
  winner: Variant | null;
}

export function ABTestDashboard() {
  const [tests, setTests] = useState<ABTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    test_id: "",
    project_id: "default",
    variant_a_title: "",
    variant_a_content: "",
    variant_b_title: "",
    variant_b_content: "",
  });

  useEffect(() => {
    fetchTests();
  }, []);

  const fetchTests = async () => {
    try {
      const res = await fetch("/api/ab-test");
      const data = await res.json();
      setTests(data.tests || []);
    } catch {
      toast("加载失败", "error");
    } finally {
      setLoading(false);
    }
  };

  const createTest = async () => {
    if (!form.test_id || !form.variant_a_title || !form.variant_b_title) {
      toast("请填写测试ID和至少两个变体标题", "error");
      return;
    }
    setCreating(true);
    try {
      const res = await fetch("/api/ab-test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          test_id: form.test_id,
          project_id: form.project_id,
          variants: [
            { title: form.variant_a_title, content: form.variant_a_content },
            { title: form.variant_b_title, content: form.variant_b_content },
          ],
        }),
      });
      if (!res.ok) {
        toast("创建失败", "error");
        return;
      }
      toast("A/B 测试已创建", "success");
      setShowForm(false);
      setForm({
        test_id: "",
        project_id: "default",
        variant_a_title: "",
        variant_a_content: "",
        variant_b_title: "",
        variant_b_content: "",
      });
      fetchTests();
    } catch {
      toast("API 服务未启动", "error");
    } finally {
      setCreating(false);
    }
  };

  const fetchResult = async (testId: string) => {
    try {
      const res = await fetch(`/api/ab-test/${testId}`);
      return await res.json();
    } catch {
      return null;
    }
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">A/B 测试</h1>
          <p className="text-muted-foreground">对比不同版本内容的表现</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="mr-2 h-4 w-4" />
          新建测试
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>创建 A/B 测试</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium">
                  测试 ID
                </label>
                <Input
                  placeholder="如: test-hook-001"
                  value={form.test_id}
                  onChange={(e) =>
                    setForm({ ...form, test_id: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">
                  项目 ID
                </label>
                <Input
                  placeholder="default"
                  value={form.project_id}
                  onChange={(e) =>
                    setForm({ ...form, project_id: e.target.value })
                  }
                />
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">变体 A</label>
                <Input
                  placeholder="标题"
                  value={form.variant_a_title}
                  onChange={(e) =>
                    setForm({ ...form, variant_a_title: e.target.value })
                  }
                />
                <Textarea
                  placeholder="内容"
                  rows={3}
                  value={form.variant_a_content}
                  onChange={(e) =>
                    setForm({ ...form, variant_a_content: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">变体 B</label>
                <Input
                  placeholder="标题"
                  value={form.variant_b_title}
                  onChange={(e) =>
                    setForm({ ...form, variant_b_title: e.target.value })
                  }
                />
                <Textarea
                  placeholder="内容"
                  rows={3}
                  value={form.variant_b_content}
                  onChange={(e) =>
                    setForm({ ...form, variant_b_content: e.target.value })
                  }
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={createTest} disabled={creating}>
                {creating ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="mr-2 h-4 w-4" />
                )}
                创建
              </Button>
              <Button variant="outline" onClick={() => setShowForm(false)}>
                取消
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {tests.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            暂无 A/B 测试，点击"新建测试"开始
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {tests.map((test) => (
            <TestCard key={test.test_id} test={test} onRefresh={fetchTests} />
          ))}
        </div>
      )}
    </div>
  );
}

function TestCard({
  test,
  onRefresh,
}: {
  test: ABTest;
  onRefresh: () => void;
}) {
  const [result, setResult] = useState<ABTest | null>(null);
  const [loadingResult, setLoadingResult] = useState(false);

  const showResult = async () => {
    setLoadingResult(true);
    const data = await fetch(`/api/ab-test/${test.test_id}`).then((r) =>
      r.json(),
    );
    setResult(data);
    setLoadingResult(false);
  };

  const totalMetrics = (v: Variant) =>
    v.metrics.views + v.metrics.likes + v.metrics.comments + v.metrics.shares;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-orange-500" />
              {test.test_id}
            </CardTitle>
            <CardDescription>
              {test.variants.length} 个变体 · {test.status}
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={showResult}>
            {loadingResult ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "查看结果"
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 md:grid-cols-2">
          {test.variants.map((v) => {
            const isWinner = result?.winner?.id === v.id;
            return (
              <div
                key={v.id}
                className={`rounded-lg border p-3 ${isWinner ? "border-green-500 bg-green-50 dark:bg-green-950/20" : ""}`}
              >
                <div className="mb-2 flex items-center gap-2">
                  <span className="font-medium">{v.title || v.id}</span>
                  {isWinner && (
                    <Badge className="bg-green-500 text-white">
                      <Trophy className="mr-1 h-3 w-3" />
                      胜出
                    </Badge>
                  )}
                </div>
                <div className="grid grid-cols-4 gap-2 text-center text-xs text-muted-foreground">
                  <div>
                    <div className="font-bold text-foreground">
                      {v.metrics.views}
                    </div>
                    曝光
                  </div>
                  <div>
                    <div className="font-bold text-foreground">
                      {v.metrics.likes}
                    </div>
                    点赞
                  </div>
                  <div>
                    <div className="font-bold text-foreground">
                      {v.metrics.comments}
                    </div>
                    评论
                  </div>
                  <div>
                    <div className="font-bold text-foreground">
                      {v.metrics.shares}
                    </div>
                    分享
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
