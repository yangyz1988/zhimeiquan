"use client";

import { useEffect, useState, useCallback, useRef } from "react";
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
import {
  Loader2,
  Plus,
  Trophy,
  BarChart3,
  Play,
  Pause,
  Square,
  Eye,
  Heart,
  MessageCircle,
  Share2,
  Bookmark,
  Clock,
  ChevronDown,
  ChevronUp,
  Trash2,
  AlertCircle,
  CheckCircle2,
  X,
  Sparkles,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  Activity,
  Target,
  FileText,
  FlaskConical,
} from "lucide-react";
import { toast } from "@/components/toaster";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Variant {
  id: string;
  title: string;
  content: string;
  metrics: {
    views: number;
    likes: number;
    comments: number;
    shares: number;
    saves?: number;
  };
  score?: number;
}

interface ABTest {
  id?: string;
  test_id: string;
  name: string;
  project_id: string;
  description?: string;
  variants: Variant[];
  status: "draft" | "running" | "paused" | "completed";
  created_at: string;
  winner?: string | null;
  confidence?: number;
  duration_days?: number;
  platforms?: string[];
}

interface CreateTestPayload {
  test_id: string;
  name: string;
  project_id: string;
  description: string;
  platforms: string[];
  variants: { title: string; content: string }[];
  duration_days: number;
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

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

const STATUS_CONFIG = {
  draft: {
    label: "草稿",
    color: "bg-gray-500/20 text-gray-400 border-gray-500/30",
    dot: "bg-gray-400",
  },
  running: {
    label: "运行中",
    color: "bg-green-500/20 text-green-400 border-green-500/30",
    dot: "bg-green-400",
  },
  paused: {
    label: "已暂停",
    color: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    dot: "bg-amber-400",
  },
  completed: {
    label: "已完成",
    color: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    dot: "bg-blue-400",
  },
};

const AUTO_REFRESH_MS = 30000;

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

function generateTestId(): string {
  const prefix = "test";
  const rand = Math.random().toString(36).substring(2, 8);
  return `${prefix}-${rand}`;
}

/** Simple engagement rate calculator */
function engagementRate(m: Variant["metrics"]): string {
  const total = m.views || 1;
  const interactions = m.likes + m.comments + m.shares + (m.saves ?? 0);
  return ((interactions / total) * 100).toFixed(2);
}

/** Compute a composite score for a variant */
function computeScore(m: Variant["metrics"]): number {
  const views = m.views || 1;
  const likeRate = m.likes / views;
  const commentRate = m.comments / views;
  const shareRate = m.shares / views;
  const saveRate = (m.saves ?? 0) / views;
  // Weighted composite
  return Math.round(
    (likeRate * 30 + commentRate * 25 + shareRate * 25 + saveRate * 20) * 100,
  );
}

/** Determine if variant A is beating variant B */
function getLeader(
  a: Variant,
  b: Variant,
): { winner: Variant; loser: Variant; margin: number } | null {
  if (!a || !b) return null;
  const scoreA = computeScore(a.metrics);
  const scoreB = computeScore(b.metrics);
  if (scoreA === scoreB) return null;
  return scoreA > scoreB
    ? { winner: a, loser: b, margin: scoreA - scoreB }
    : { winner: b, loser: a, margin: scoreB - scoreA };
}

/* ------------------------------------------------------------------ */
/*  Main Dashboard Component                                           */
/* ------------------------------------------------------------------ */

export function ABTestDashboard() {
  const [tests, setTests] = useState<ABTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Detail view
  const [selectedTest, setSelectedTest] = useState<ABTest | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Auto-refresh
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchTests = useCallback(async () => {
    try {
      setError(null);
      const res = await fetch("/api/ab-test");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setTests(data.tests || []);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "未知错误";
      setError(msg);
      toast("加载测试列表失败: " + msg, "error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTests();
  }, [fetchTests]);

  // Manual refresh
  const handleRefresh = useCallback(() => {
    setLoading(true);
    fetchTests();
  }, [fetchTests]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">A/B 测试</h1>
          <p className="mt-1 text-sm text-white/50">
            科学对比不同内容变体的表现，找出最优方案
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={loading}
            className="border-white/10"
          >
            <RefreshCw
              className={`mr-1 h-4 w-4 ${loading ? "animate-spin" : ""}`}
            />
            {loading ? "刷新中..." : "刷新"}
          </Button>
          <Button
            onClick={() => setShowCreateModal(true)}
            className="bg-gradient-to-r from-orange-500 to-pink-500 text-white shadow-lg hover:from-orange-600 hover:to-pink-600"
          >
            <Plus className="mr-1 h-4 w-4" />
            新建测试
          </Button>
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <CreateTestModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false);
            fetchTests();
          }}
        />
      )}

      {/* Detail Panel */}
      {selectedTest && (
        <TestDetailPanel
          test={selectedTest}
          onClose={() => setSelectedTest(null)}
          onRefresh={fetchTests}
          onStatusChange={() => {
            fetchTests();
          }}
        />
      )}

      {/* Content */}
      {loading && tests.length === 0 ? (
        <div className="space-y-4">
          {/* Summary bar skeleton */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="glass-card h-16 animate-pulse border-white/5" />
            ))}
          </div>
          {/* Test cards skeleton */}
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="glass-card h-64 animate-pulse border-white/5" />
            ))}
          </div>
        </div>
      ) : error && tests.length === 0 ? (
        <Card className="glass-card border-red-500/20">
          <CardContent className="flex flex-col items-center gap-3 py-12">
            <AlertCircle className="h-10 w-10 text-red-400" />
            <p className="text-sm text-white/60">加载失败: {error}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              className="border-white/10"
            >
              <RefreshCw className="mr-1 h-4 w-4" />
              重试
            </Button>
          </CardContent>
        </Card>
      ) : tests.length === 0 ? (
        <EmptyState onCreate={() => setShowCreateModal(true)} />
      ) : (
        <>
          {/* Summary Stats */}
          <TestSummaryBar tests={tests} />

          {/* Test Cards */}
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {tests.map((test) => (
              <TestCard
                key={test.test_id}
                test={test}
                onViewDetail={() => setSelectedTest(test)}
                onRefresh={fetchTests}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Summary Stats Bar                                                  */
/* ------------------------------------------------------------------ */

function TestSummaryBar({ tests }: { tests: ABTest[] }) {
  const total = tests.length;
  const running = tests.filter((t) => t.status === "running").length;
  const completed = tests.filter((t) => t.status === "completed").length;
  const draft = tests.filter((t) => t.status === "draft").length;

  const items = [
    { label: "全部", value: total, color: "text-white", glow: "glow-blue" },
    {
      label: "运行中",
      value: running,
      color: "text-green-400",
      glow: "glow-green",
    },
    {
      label: "已完成",
      value: completed,
      color: "text-blue-400",
      glow: "glow-blue",
    },
    { label: "草稿", value: draft, color: "text-gray-400", glow: "glow-orange" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label} className={`glass-card ${item.glow}`}>
          <CardContent className="flex flex-col items-center py-3 text-center">
            <span className={`text-2xl font-bold ${item.color}`}>
              {item.value}
            </span>
            <span className="text-xs text-white/40">{item.label}</span>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Empty State                                                        */
/* ------------------------------------------------------------------ */

function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <Card className="glass-card overflow-hidden border-white/5">
      <CardContent className="flex flex-col items-center gap-4 py-16">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-orange-500/20 to-pink-500/20">
          <FlaskConical className="h-8 w-8 text-orange-400" />
        </div>
        <div className="text-center">
          <h3 className="text-lg font-medium text-white/80">还没有A/B测试</h3>
          <p className="mt-1 text-sm text-white/40">
            创建你的第一个测试，开始优化内容表现
          </p>
        </div>
        <Button
          onClick={onCreate}
          className="bg-gradient-to-r from-orange-500 to-pink-500 text-white shadow-lg hover:from-orange-600 hover:to-pink-600"
        >
          <Plus className="mr-1 h-4 w-4" />
          创建测试
        </Button>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Create Test Modal                                                  */
/* ------------------------------------------------------------------ */

function CreateTestModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [testId] = useState(generateTestId);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [platforms, setPlatforms] = useState<string[]>(["抖音", "小红书"]);
  const [varATitle, setVarATitle] = useState("");
  const [varAContent, setVarAContent] = useState("");
  const [varBTitle, setVarBTitle] = useState("");
  const [varBContent, setVarBContent] = useState("");
  const [durationDays, setDurationDays] = useState(7);
  const [creating, setCreating] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const togglePlatform = (p: string) => {
    setPlatforms((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p],
    );
  };

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = "请输入测试名称";
    if (platforms.length === 0) errs.platforms = "请至少选择一个平台";
    if (!varATitle.trim()) errs.varA = "请输入变体A标题";
    if (!varAContent.trim()) errs.varAContent = "请输入变体A内容";
    if (!varBTitle.trim()) errs.varB = "请输入变体B标题";
    if (!varBContent.trim()) errs.varBContent = "请输入变体B内容";
    if (durationDays < 1 || durationDays > 90) errs.duration = "时长应在1-90天之间";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleCreate = async () => {
    if (!validate()) return;

    setCreating(true);
    try {
      const payload: CreateTestPayload = {
        test_id: testId,
        name: name.trim(),
        project_id: "default",
        description: description.trim(),
        platforms,
        variants: [
          { title: varATitle.trim(), content: varAContent.trim() },
          { title: varBTitle.trim(), content: varBContent.trim() },
        ],
        duration_days: durationDays,
      };

      const res = await fetch("/api/ab-test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.message || `HTTP ${res.status}`);
      }

      toast("A/B 测试已创建成功", "success");
      onCreated();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "API 服务未启动";
      toast("创建失败: " + msg, "error");
    } finally {
      setCreating(false);
    }
  };

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto pt-10 pb-10">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      {/* Modal */}
      <div className="relative z-10 w-full max-w-2xl animate-in zoom-in-95 fade-in">
        <Card className="glass-card border-white/10 shadow-2xl">
          <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-4">
            <div>
              <CardTitle className="flex items-center gap-2 text-xl">
                <FlaskConical className="h-5 w-5 text-orange-400" />
                创建 A/B 测试
              </CardTitle>
              <CardDescription className="mt-1">
                对比两个内容变体的表现，找出最优版本
              </CardDescription>
            </div>
            <button
              onClick={onClose}
              className="rounded-lg p-1 text-white/40 transition-colors hover:bg-white/5 hover:text-white/80"
            >
              <X className="h-5 w-5" />
            </button>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Test ID (auto) */}
            <div className="flex items-center gap-2 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2">
              <span className="text-xs text-white/40">测试ID</span>
              <code className="text-xs text-orange-400">{testId}</code>
            </div>

            {/* Name */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-white/70">
                测试名称 <span className="text-red-400">*</span>
              </label>
              <Input
                placeholder="例如: 标题风格对比测试"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className={`border-white/10 bg-white/5 text-white placeholder:text-white/20 ${
                  errors.name ? "border-red-500" : ""
                }`}
              />
              {errors.name && (
                <p className="mt-1 text-xs text-red-400">{errors.name}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-white/70">
                描述
              </label>
              <Textarea
                placeholder="测试目的、假设等说明"
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="border-white/10 bg-white/5 text-white placeholder:text-white/20"
              />
            </div>

            {/* Platforms */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-white/70">
                目标平台 <span className="text-red-400">*</span>
              </label>
              <div className="flex flex-wrap gap-2">
                {PLATFORMS.map((p) => (
                  <Badge
                    key={p}
                    variant={platforms.includes(p) ? "default" : "outline"}
                    className={`cursor-pointer transition-all ${
                      platforms.includes(p)
                        ? "border-orange-500/30 bg-orange-500/20 text-orange-300"
                        : "border-white/10 text-white/40 hover:border-white/20 hover:text-white/60"
                    }`}
                    onClick={() => togglePlatform(p)}
                  >
                    {p}
                    {platforms.includes(p) && (
                      <span className="ml-1 text-orange-300">&#10003;</span>
                    )}
                  </Badge>
                ))}
              </div>
              {errors.platforms && (
                <p className="mt-1 text-xs text-red-400">{errors.platforms}</p>
              )}
            </div>

            {/* Variants */}
            <div className="grid gap-4 md:grid-cols-2">
              {/* Variant A */}
              <div className="space-y-3 rounded-lg border border-white/5 bg-gradient-to-br from-orange-500/5 to-transparent p-4">
                <div className="flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-orange-500 to-pink-500 text-xs font-bold text-white">
                    A
                  </span>
                  <span className="text-sm font-medium text-white/70">
                    变体 A
                  </span>
                </div>
                <Input
                  placeholder="标题"
                  value={varATitle}
                  onChange={(e) => setVarATitle(e.target.value)}
                  className={`border-white/10 bg-white/5 text-white placeholder:text-white/20 ${
                    errors.varA ? "border-red-500" : ""
                  }`}
                />
                <Textarea
                  placeholder="内容正文"
                  rows={4}
                  value={varAContent}
                  onChange={(e) => setVarAContent(e.target.value)}
                  className={`border-white/10 bg-white/5 text-white placeholder:text-white/20 ${
                    errors.varAContent ? "border-red-500" : ""
                  }`}
                />
                {errors.varA && (
                  <p className="text-xs text-red-400">{errors.varA}</p>
                )}
                {errors.varAContent && (
                  <p className="text-xs text-red-400">{errors.varAContent}</p>
                )}
              </div>

              {/* Variant B */}
              <div className="space-y-3 rounded-lg border border-white/5 bg-gradient-to-br from-blue-500/5 to-transparent p-4">
                <div className="flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 text-xs font-bold text-white">
                    B
                  </span>
                  <span className="text-sm font-medium text-white/70">
                    变体 B
                  </span>
                </div>
                <Input
                  placeholder="标题"
                  value={varBTitle}
                  onChange={(e) => setVarBTitle(e.target.value)}
                  className={`border-white/10 bg-white/5 text-white placeholder:text-white/20 ${
                    errors.varB ? "border-red-500" : ""
                  }`}
                />
                <Textarea
                  placeholder="内容正文"
                  rows={4}
                  value={varBContent}
                  onChange={(e) => setVarBContent(e.target.value)}
                  className={`border-white/10 bg-white/5 text-white placeholder:text-white/20 ${
                    errors.varBContent ? "border-red-500" : ""
                  }`}
                />
                {errors.varB && (
                  <p className="text-xs text-red-400">{errors.varB}</p>
                )}
                {errors.varBContent && (
                  <p className="text-xs text-red-400">{errors.varBContent}</p>
                )}
              </div>
            </div>

            {/* Duration */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-white/70">
                测试时长（天）
              </label>
              <div className="flex items-center gap-3">
                <Input
                  type="number"
                  min={1}
                  max={90}
                  value={durationDays}
                  onChange={(e) =>
                    setDurationDays(Number(e.target.value) || 7)
                  }
                  className={`w-24 border-white/10 bg-white/5 text-white ${
                    errors.duration ? "border-red-500" : ""
                  }`}
                />
                <span className="text-sm text-white/40">
                  建议 7-14 天以获得统计显著性
                </span>
              </div>
              {errors.duration && (
                <p className="mt-1 text-xs text-red-400">{errors.duration}</p>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 border-t border-white/5 pt-4">
              <Button
                variant="outline"
                onClick={onClose}
                className="border-white/10 text-white/70 hover:bg-white/5"
              >
                取消
              </Button>
              <Button
                onClick={handleCreate}
                disabled={creating}
                className="bg-gradient-to-r from-orange-500 to-pink-500 text-white shadow-lg hover:from-orange-600 hover:to-pink-600"
              >
                {creating ? (
                  <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="mr-1 h-4 w-4" />
                )}
                创建测试
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Test Card                                                          */
/* ------------------------------------------------------------------ */

function TestCard({
  test,
  onViewDetail,
  onRefresh,
}: {
  test: ABTest;
  onViewDetail: () => void;
  onRefresh: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const cfg = STATUS_CONFIG[test.status] || STATUS_CONFIG.draft;

  const completedDays = test.duration_days
    ? Math.min(
        Math.floor(
          (Date.now() - new Date(test.created_at).getTime()) /
            (1000 * 60 * 60 * 24),
        ),
        test.duration_days,
      )
    : null;

  const progress =
    test.duration_days && completedDays !== null
      ? Math.round((completedDays / test.duration_days) * 100)
      : null;

  return (
    <Card className="glass-card glow-orange overflow-hidden border-white/5 transition-all hover:border-white/10">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <BarChart3 className="h-4 w-4 text-orange-400" />
                <span className="truncate">{test.name || test.test_id}</span>
              </CardTitle>
            </div>
            <CardDescription className="mt-1 flex flex-wrap items-center gap-2">
              <Badge
                className={`border ${cfg.color}`}
                variant="outline"
              >
                <span className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
                {cfg.label}
              </Badge>
              <span className="text-xs text-white/30">
                {formatDate(test.created_at)}
              </span>
              {test.duration_days && (
                <span className="text-xs text-white/30">
                  {test.duration_days}天测试
                </span>
              )}
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="ml-2 text-white/40 hover:text-white/80"
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        {/* Progress bar */}
        {test.status === "running" && progress !== null && (
          <div className="mb-3">
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="text-white/40">进度</span>
              <span className="text-white/60">
                {completedDays}/{test.duration_days} 天 ({progress}%)
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/5">
              <div
                className="h-full rounded-full bg-gradient-to-r from-orange-500 to-pink-500 transition-all duration-500"
                style={{ width: `${Math.min(progress, 100)}%` }}
              />
            </div>
          </div>
        )}

        {/* Variant preview */}
        <div className="grid gap-2 md:grid-cols-2">
          {test.variants.slice(0, 2).map((v, idx) => {
            const label = idx === 0 ? "A" : "B";
            const isWinner = test.winner === v.id;
            const score = computeScore(v.metrics);
            const isLeading =
              test.variants.length === 2 &&
              test.status === "running" &&
              getLeader(test.variants[0], test.variants[1])?.winner.id === v.id;

            return (
              <div
                key={v.id}
                className={`rounded-lg border p-3 transition-all ${
                  isWinner
                    ? "border-green-500/30 bg-green-500/5"
                    : isLeading
                      ? "border-orange-500/20 bg-orange-500/5"
                      : "border-white/5 bg-white/[0.02]"
                }`}
              >
                <div className="mb-1 flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`flex h-5 w-5 items-center justify-center rounded text-[10px] font-bold ${
                        idx === 0
                          ? "bg-gradient-to-br from-orange-500 to-pink-500 text-white"
                          : "bg-gradient-to-br from-blue-500 to-cyan-500 text-white"
                      }`}
                    >
                      {label}
                    </span>
                    <span className="truncate text-sm font-medium text-white/70">
                      {v.title || v.id}
                    </span>
                  </div>
                  {isWinner && (
                    <Badge className="border-green-500/30 bg-green-500/20 text-green-400">
                      <Trophy className="mr-0.5 h-3 w-3" />
                      胜出
                    </Badge>
                  )}
                  {isLeading && !isWinner && (
                    <Badge className="border-orange-500/30 bg-orange-500/20 text-orange-400">
                      <TrendingUp className="mr-0.5 h-3 w-3" />
                      领先
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs text-white/40">
                  <span className="flex items-center gap-1">
                    <Eye className="h-3 w-3" />
                    {v.metrics.views}
                  </span>
                  <span className="flex items-center gap-1">
                    <Heart className="h-3 w-3" />
                    {v.metrics.likes}
                  </span>
                  <span className="flex items-center gap-1">
                    <MessageCircle className="h-3 w-3" />
                    {v.metrics.comments}
                  </span>
                  <span className="flex items-center gap-1">
                    <Share2 className="h-3 w-3" />
                    {v.metrics.shares}
                  </span>
                </div>
                <div className="mt-1 text-[10px] text-white/30">
                  综合得分: {score}
                </div>
              </div>
            );
          })}
        </div>

        {/* Actions */}
        <div className="mt-3 flex items-center justify-end gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onViewDetail}
            className="text-white/50 hover:text-white/80"
          >
            <Activity className="mr-1 h-3.5 w-3.5" />
            详情
          </Button>
          <StatusActions test={test} onRefresh={onRefresh} />
        </div>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Status Action Buttons                                              */
/* ------------------------------------------------------------------ */

function StatusActions({
  test,
  onRefresh,
}: {
  test: ABTest;
  onRefresh: () => void;
}) {
  const [busy, setBusy] = useState(false);

  const updateStatus = async (newStatus: string) => {
    setBusy(true);
    try {
      const res = await fetch(`/api/ab-test/${test.test_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      toast(
        `测试已${newStatus === "running" ? "启动" : newStatus === "paused" ? "暂停" : "结束"}`,
        "success",
      );
      onRefresh();
    } catch {
      toast("操作失败", "error");
    } finally {
      setBusy(false);
    }
  };

  if (test.status === "draft") {
    return (
      <Button
        size="sm"
        disabled={busy}
        onClick={() => updateStatus("running")}
        className="bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:from-green-600 hover:to-emerald-600"
      >
        {busy ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <Play className="mr-1 h-3.5 w-3.5" />
        )}
        开始
      </Button>
    );
  }

  if (test.status === "running") {
    return (
      <div className="flex gap-1.5">
        <Button
          variant="outline"
          size="sm"
          disabled={busy}
          onClick={() => updateStatus("paused")}
          className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10"
        >
          {busy ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Pause className="mr-1 h-3.5 w-3.5" />
          )}
          暂停
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={busy}
          onClick={() => updateStatus("completed")}
          className="border-red-500/30 text-red-400 hover:bg-red-500/10"
        >
          {busy ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Square className="mr-1 h-3.5 w-3.5" />
          )}
          结束
        </Button>
      </div>
    );
  }

  if (test.status === "paused") {
    return (
      <Button
        size="sm"
        disabled={busy}
        onClick={() => updateStatus("running")}
        className="bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:from-green-600 hover:to-emerald-600"
      >
        {busy ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <Play className="mr-1 h-3.5 w-3.5" />
        )}
        恢复
      </Button>
    );
  }

  return null;
}

/* ------------------------------------------------------------------ */
/*  Test Detail Panel                                                  */
/* ------------------------------------------------------------------ */

function TestDetailPanel({
  test,
  onClose,
  onRefresh,
  onStatusChange,
}: {
  test: ABTest;
  onClose: () => void;
  onRefresh: () => void;
  onStatusChange: () => void;
}) {
  const [detail, setDetail] = useState<ABTest | null>(test);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(
    test.status === "running" || test.status === "paused",
  );
  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);
  const cfg = STATUS_CONFIG[detail?.status || test.status] || STATUS_CONFIG.draft;

  // Expiry check
  const isExpired = useCallback(() => {
    if (!detail?.duration_days || !detail?.created_at) return false;
    const created = new Date(detail.created_at).getTime();
    const elapsed = (Date.now() - created) / (1000 * 60 * 60 * 24);
    return elapsed >= detail.duration_days;
  }, [detail]);

  const fetchDetail = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/ab-test/${test.test_id}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setDetail(data);

      // Auto-complete if expired
      if (data.status === "running" && isExpired()) {
        await fetch(`/api/ab-test/${test.test_id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: "completed" }),
        });
        onStatusChange();
        toast("测试时长已到，已自动完成", "info");
        onRefresh();
      }
    } catch {
      // silent fail on auto-refresh
    } finally {
      setLoading(false);
    }
  }, [test.test_id, isExpired, onStatusChange, onRefresh]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh && (detail?.status === "running" || detail?.status === "paused")) {
      refreshTimerRef.current = setInterval(fetchDetail, AUTO_REFRESH_MS);
    }
    return () => {
      if (refreshTimerRef.current) clearInterval(refreshTimerRef.current);
    };
  }, [autoRefresh, detail?.status, fetchDetail]);

  // Initial fetch if needed
  useEffect(() => {
    if (!detail?.variants?.length) fetchDetail();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const variants = detail?.variants || [];
  const varA = variants[0];
  const varB = variants[1];
  const leader = varA && varB ? getLeader(varA, varB) : null;

  return (
    <Card className="glass-card overflow-hidden border-white/5">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 border-b border-white/5 pb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <CardTitle className="text-lg">
              {detail?.name || detail?.test_id}
            </CardTitle>
            <Badge className={`border ${cfg.color}`} variant="outline">
              <span className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
              {cfg.label}
            </Badge>
          </div>
          <CardDescription className="mt-1 flex items-center gap-3">
            <span>{formatDate(detail?.created_at || test.created_at)}</span>
            {detail?.duration_days && (
              <span>{detail.duration_days} 天测试周期</span>
            )}
            {detail?.platforms && detail.platforms.length > 0 && (
              <span>{detail.platforms.join(" / ")}</span>
            )}
          </CardDescription>
        </div>
        <div className="flex items-center gap-2">
          {/* Auto-refresh toggle */}
          {(detail?.status === "running" || detail?.status === "paused") && (
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`rounded-lg p-1.5 transition-colors ${
                autoRefresh
                  ? "text-green-400 hover:bg-green-500/10"
                  : "text-white/30 hover:bg-white/5"
              }`}
              title={autoRefresh ? "自动刷新已开启" : "自动刷新已关闭"}
            >
              <RefreshCw
                className={`h-4 w-4 ${autoRefresh ? "animate-spin" : ""}`}
              />
            </button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchDetail}
            disabled={loading}
            className="text-white/50 hover:text-white/80"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-white/50 hover:text-white/80"
          >
            <X className="h-4 w-4" />
            关闭
          </Button>
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        {detail?.description && (
          <p className="mb-4 text-sm text-white/50">{detail.description}</p>
        )}

        {variants.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-orange-400" />
            <span className="ml-2 text-sm text-white/40">加载详情中...</span>
          </div>
        ) : (
          <>
            {/* Winner Banner */}
            {(detail?.status === "completed" || isExpired()) && leader && (
              <div className="mb-4 overflow-hidden rounded-lg border border-green-500/20 bg-gradient-to-r from-green-500/10 to-emerald-500/5">
                <div className="flex items-center gap-3 p-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-yellow-500">
                    <Trophy className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <p className="font-medium text-green-400">测试已完成</p>
                    <p className="text-sm text-green-400/70">
                      胜出: {leader.winner.title || leader.winner.id} —
                      综合得分领先 {leader.margin} 分
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Duration expired but not yet completed */}
            {detail?.status === "running" && isExpired() && (
              <div className="mb-4 overflow-hidden rounded-lg border border-amber-500/20 bg-gradient-to-r from-amber-500/10 to-orange-500/5 p-4">
                <div className="flex items-center gap-3">
                  <Clock className="h-5 w-5 text-amber-400" />
                  <div>
                    <p className="font-medium text-amber-400">测试周期已到</p>
                    <p className="text-sm text-amber-400/70">
                      建议结束测试查看最终结果
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Live Indicator */}
            {detail?.status === "running" && !isExpired() && (
              <div className="mb-4 flex items-center gap-2 text-xs text-green-400/70">
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-green-400" />
                实时更新中{autoRefresh ? "（自动刷新每30秒）" : ""}
              </div>
            )}

            {/* Side-by-side comparison */}
            <div className="grid gap-4 md:grid-cols-2">
              {variants.map((v, idx) => {
                const label = idx === 0 ? "A" : "B";
                const isWinner = leader?.winner.id === v.id;
                const score = computeScore(v.metrics);
                const maxScore = leader ? computeScore(leader.winner.metrics) : score;
                const scorePct = maxScore > 0 ? (score / maxScore) * 100 : 0;

                return (
                  <div
                    key={v.id}
                    className={`rounded-xl border p-5 transition-all ${
                      isWinner
                        ? "border-green-500/30 bg-gradient-to-br from-green-500/5 to-transparent"
                        : idx === 0
                          ? "border-white/5 bg-gradient-to-br from-orange-500/[0.03] to-transparent"
                          : "border-white/5 bg-gradient-to-br from-blue-500/[0.03] to-transparent"
                    }`}
                  >
                    {/* Variant Header */}
                    <div className="mb-4 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={`flex h-7 w-7 items-center justify-center rounded-md text-sm font-bold text-white ${
                            idx === 0
                              ? "bg-gradient-to-br from-orange-500 to-pink-500"
                              : "bg-gradient-to-br from-blue-500 to-cyan-500"
                          }`}
                        >
                          {label}
                        </span>
                        <span className="font-medium text-white/80">
                          {v.title || v.id}
                        </span>
                      </div>
                      {isWinner && (
                        <Badge className="border-green-500/30 bg-green-500/20 text-green-400">
                          <Trophy className="mr-1 h-3 w-3" />
                          胜出
                        </Badge>
                      )}
                      {leader && !isWinner && (
                        <Badge
                          variant="outline"
                          className="border-white/10 text-white/40"
                        >
                          落后 {leader.margin} 分
                        </Badge>
                      )}
                    </div>

                    {/* Content preview */}
                    {v.content && (
                      <div className="mb-4 rounded-lg border border-white/5 bg-white/[0.02] p-3">
                        <p className="text-xs leading-relaxed text-white/50 line-clamp-3">
                          {v.content}
                        </p>
                      </div>
                    )}

                    {/* Metric Cards */}
                    <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
                      <MetricStat
                        icon={Eye}
                        label="曝光"
                        value={v.metrics.views}
                        color="text-blue-400"
                      />
                      <MetricStat
                        icon={Heart}
                        label="点赞"
                        value={v.metrics.likes}
                        color="text-red-400"
                      />
                      <MetricStat
                        icon={MessageCircle}
                        label="评论"
                        value={v.metrics.comments}
                        color="text-green-400"
                      />
                      <MetricStat
                        icon={Share2}
                        label="分享"
                        value={v.metrics.shares}
                        color="text-orange-400"
                      />
                      {v.metrics.saves !== undefined && (
                        <MetricStat
                          icon={Bookmark}
                          label="收藏"
                          value={v.metrics.saves}
                          color="text-purple-400"
                        />
                      )}
                      <MetricStat
                        icon={Activity}
                        label="互动率"
                        value={`${engagementRate(v.metrics)}%`}
                        color="text-pink-400"
                      />
                    </div>

                    {/* Score bar */}
                    <div>
                      <div className="mb-1 flex items-center justify-between text-xs">
                        <span className="text-white/40">综合得分</span>
                        <span className="font-bold text-orange-400">
                          {score}
                        </span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
                        <div
                          className={`h-full rounded-full transition-all duration-700 ${
                            isWinner
                              ? "bg-gradient-to-r from-green-400 to-emerald-400"
                              : "bg-gradient-to-r from-orange-500 to-pink-500"
                          }`}
                          style={{ width: `${scorePct}%` }}
                        />
                      </div>
                    </div>

                    {/* Metric trend bars */}
                    {detail?.status === "running" && (
                      <div className="mt-4 space-y-2 border-t border-white/5 pt-4">
                        <p className="text-[10px] font-medium uppercase tracking-wider text-white/30">
                          指标对比
                        </p>
                        <MetricBar
                          label="曝光"
                          value={v.metrics.views}
                          max={Math.max(
                            ...variants.map((x) => x.metrics.views),
                            1,
                          )}
                          color="bg-blue-500"
                        />
                        <MetricBar
                          label="点赞"
                          value={v.metrics.likes}
                          max={Math.max(
                            ...variants.map((x) => x.metrics.likes),
                            1,
                          )}
                          color="bg-red-500"
                        />
                        <MetricBar
                          label="评论"
                          value={v.metrics.comments}
                          max={Math.max(
                            ...variants.map((x) => x.metrics.comments),
                            1,
                          )}
                          color="bg-green-500"
                        />
                        <MetricBar
                          label="分享"
                          value={v.metrics.shares}
                          max={Math.max(
                            ...variants.map((x) => x.metrics.shares),
                            1,
                          )}
                          color="bg-orange-500"
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Status actions */}
            <div className="mt-4 flex items-center justify-end gap-2 border-t border-white/5 pt-4">
              <StatusActions test={detail || test} onRefresh={onRefresh} />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Sub-components                                                     */
/* ------------------------------------------------------------------ */

function MetricStat({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2.5 text-center">
      <Icon className={`mx-auto mb-0.5 h-3.5 w-3.5 ${color}`} />
      <div className="text-sm font-bold text-white/80">{value}</div>
      <div className="text-[10px] text-white/30">{label}</div>
    </div>
  );
}

function MetricBar({
  label,
  value,
  max,
  color,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="flex items-center gap-2">
      <span className="w-8 text-[10px] text-white/40">{label}</span>
      <div className="flex-1 h-1.5 overflow-hidden rounded-full bg-white/5">
        <div
          className={`h-full rounded-full ${color} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-12 text-right text-[10px] text-white/60">
        {value.toLocaleString()}
      </span>
    </div>
  );
}

export default ABTestDashboard;
