"use client";

import { useState, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Sparkles, Copy, Check, Video, Play, Pause, Terminal, Trash2, ClipboardPaste, Clock, Save } from "lucide-react";
import { toast } from "@/components/toaster";
import { VideoPreview } from "@/components/video-preview";

// 13个平台全覆盖：短视频(抖音/快手/视频号/TikTok/Instagram)、中长视频(B站/YouTube)、种草(小红书)、图文(微博/知乎/头条/公众号/百度热搜)
const CONTENT_TYPES = [
  { id: "text", label: "图文内容", platforms: ["小红书", "微博", "公众号", "知乎", "头条", "百度热搜"] },
  { id: "video", label: "视频内容", platforms: ["抖音", "快手", "视频号", "B站", "YouTube", "TikTok", "Instagram"] },
];
const PERSONAS = ["学长型", "专家型", "闺蜜型", "老铁型", "导师型", "吐槽型", "故事型", "干货型"];
const FIRE_SCORE_LEVELS = [
  { id: "lv4", label: "Lv4 通杀", desc: "70+", color: "text-blue-400", glow: "shadow-[0_0_12px_rgba(59,130,246,0.3)]" },
  { id: "lv3", label: "Lv3 小爆", desc: "80+", color: "text-green-400", glow: "shadow-[0_0_12px_rgba(34,197,94,0.3)]" },
  { id: "lv2", label: "Lv2 大爆", desc: "90+", color: "text-orange-400", glow: "shadow-[0_0_12px_rgba(249,115,22,0.3)]" },
  { id: "lv1", label: "Lv1 爆款", desc: "95+", color: "text-red-400", glow: "shadow-[0_0_12px_rgba(239,68,68,0.3)]" },
];
const COVER_STYLES = ["自动", "大字报", "对比拼图", "极简"];

interface GenerateResult {
  titles: string[];
  script: string;
  tags: string[];
  hook: string;
}

interface StreamEvent {
  event: string;
  data: unknown;
}

export function GenerateForm() {
  const [topic, setTopic] = useState("");
  const [platform, setPlatform] = useState("抖音");
  const [persona, setPersona] = useState("学长型");
  const [duration, setDuration] = useState(60);
  const [contentType, setContentType] = useState("video");
  const [fireScoreLevel, setFireScoreLevel] = useState("lv3");
  const [coverStyle, setCoverStyle] = useState("自动");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [copied, setCopied] = useState(false);
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoResult, setVideoResult] = useState<{ video_url: string } | null>(null);

  // Recent topics and draft state
  const [recentTopics, setRecentTopics] = useState<string[]>(() => {
    if (typeof window !== "undefined") {
      try {
        return JSON.parse(localStorage.getItem("gen_recent_topics") || "[]");
      } catch {
        return [];
      }
    }
    return [];
  });
  const [showTopicDropdown, setShowTopicDropdown] = useState(false);
  const [draftTopic, setDraftTopic] = useState("");
  const [showDraftSaved, setShowDraftSaved] = useState(false);
  const [progressDisplay, setProgressDisplay] = useState(0);

  // SSE 流式状态
  const [useStreaming, setUseStreaming] = useState(true);
  const [streamStatus, setStreamStatus] = useState<string>("");
  const [streamModel, setStreamModel] = useState<string>("");
  const [streamProgress, setStreamProgress] = useState(0);
  const [streamTitles, setStreamTitles] = useState<string[]>([]);
  const [streamScript, setStreamScript] = useState<string>("");
  const abortControllerRef = useRef<AbortController | null>(null);

  const resetStreamState = useCallback(() => {
    setStreamStatus("");
    setStreamModel("");
    setStreamProgress(0);
    setStreamTitles([]);
    setStreamScript("");
    setResult(null);
  }, []);

  /* ---- New helper functions ---- */

  const saveRecentTopic = (t: string) => {
    if (!t.trim()) return;
    setRecentTopics((prev) => {
      const filtered = [t, ...prev.filter((p) => p !== t)].slice(0, 10);
      try { localStorage.setItem("gen_recent_topics", JSON.stringify(filtered)); } catch { /* noop */ }
      return filtered;
    });
  };

  const handleClear = () => {
    setTopic("");
    setResult(null);
    setStreamScript("");
    setStreamTitles([]);
    setVideoResult(null);
    setVideoLoading(false);
    setProgressDisplay(0);
    toast("表单已清空");
  };

  const handlePasteFromClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text.trim()) {
        setTopic(text.trim());
        toast("已从剪贴板粘贴");
      } else {
        toast("剪贴板为空", "error");
      }
    } catch {
      toast("无法读取剪贴板", "error");
    }
  };

  const handleSaveDraft = () => {
    const draft = { topic, platform, persona, duration, contentType, fireScoreLevel, coverStyle, saved_at: new Date().toISOString() };
    try {
      localStorage.setItem("gen_draft", JSON.stringify(draft));
      setShowDraftSaved(true);
      toast("草稿已保存");
      setTimeout(() => setShowDraftSaved(false), 2000);
    } catch {
      toast("保存草稿失败", "error");
    }
  };

  const handleSelectRecentTopic = (t: string) => {
    setTopic(t);
    setShowTopicDropdown(false);
  };

  const loadDraft = () => {
    try {
      const raw = localStorage.getItem("gen_draft");
      if (raw) {
        const d = JSON.parse(raw);
        setTopic(d.topic || "");
        setPlatform(d.platform || "抖音");
        setPersona(d.persona || "学长型");
        setDuration(d.duration ?? 60);
        setContentType(d.contentType || "video");
        setFireScoreLevel(d.fireScoreLevel || "lv3");
        setCoverStyle(d.coverStyle || "自动");
        toast("草稿已恢复");
      } else {
        toast("没有保存的草稿", "error");
      }
    } catch {
      toast("恢复草稿失败", "error");
    }
  };

  const handleGenerateStreaming = async () => {
    if (!topic.trim()) return;
    saveRecentTopic(topic);
    resetStreamState();
    setLoading(true);
    setUseStreaming(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const res = await fetch("/api/stream/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          platform,
          persona,
          duration,
          priority: "balanced",
        }),
        signal: controller.signal,
      });

      if (!res.ok) {
        toast("流式生成失败，状态码: " + res.status, "error");
        setLoading(false);
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        toast("无法读取流式响应", "error");
        setLoading(false);
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";
      let finalResult: GenerateResult = { titles: [], script: "", tags: [], hook: "" };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || ""; // 保留部分行

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const parsed: StreamEvent = JSON.parse(line.slice(6));
            handleStreamEvent(parsed, finalResult);
          } catch {
            // 跳过无法解析的消息
          }
        }
      }

      // 处理剩余 buffer
      if (buffer.startsWith("data: ")) {
        try {
          const parsed: StreamEvent = JSON.parse(buffer.slice(6));
          handleStreamEvent(parsed, finalResult);
        } catch {
          // ignore
        }
      }

      // 如果有最终结果，设置到 result
      if (finalResult.script) {
        setResult(finalResult);
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== "AbortError") {
        toast("流式生成失败，请检查网络后重试", "error");
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleStreamEvent = (parsed: StreamEvent, finalResult: GenerateResult) => {
    const { event, data } = parsed;
    const payload = data as Record<string, unknown>;

    switch (event) {
      case "status":
        setStreamStatus((payload.message as string) || "");
        if (typeof payload.progress === "number") {
          const p = payload.progress;
          setStreamProgress(p);
          setProgressDisplay(p);
        }
        break;

      case "model":
        setStreamModel((payload.model_name as string) || (payload.model as string) || "");
        break;

      case "title":
        if (payload.title) {
          setStreamTitles((prev) => {
            if (prev.includes(payload.title as string)) return prev;
            return [...prev, payload.title as string];
          });
        }
        break;

      case "chunk":
        if (payload.text) {
          setStreamScript((prev) => prev + (payload.text as string));
        }
        break;

      case "complete":
        setProgressDisplay(100);
        if (payload.titles) finalResult.titles = payload.titles as string[];
        if (payload.script) finalResult.script = payload.script as string;
        if (payload.tags) finalResult.tags = payload.tags as string[];
        if (payload.hook) finalResult.hook = payload.hook as string;
        break;

      case "error":
        toast((payload.message as string) || "生成错误", "error");
        break;
    }
  };

  const handleGenerateLegacy = async () => {
    if (!topic.trim()) return;
    saveRecentTopic(topic);
    resetStreamState();
    setLoading(true);
    setUseStreaming(false);

    try {
      const res = await fetch("/api/content/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, platform, persona, duration, contentType, fireScoreLevel, coverStyle }),
      });
      const data = await res.json();
      setResult(data);
    } catch {
      toast("生成失败，请检查网络后重试", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (useStreaming) {
      await handleGenerateStreaming();
    } else {
      await handleGenerateLegacy();
    }
  };

  const handleAbort = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setLoading(false);
      toast("已取消生成");
    }
  };

  const copyScript = () => {
    const script = result?.script || streamScript;
    if (script) {
      navigator.clipboard.writeText(script);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleGenerateVideo = async () => {
    const script = result?.script || streamScript;
    const title = result?.titles?.[0] || streamTitles?.[0];
    if (!script || !title) return;

    setVideoLoading(true);
    try {
      const res = await fetch("/api/video/digital-human", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ script, title, platform, persona, duration }),
      });
      const data = await res.json();
      if (data.video_url) {
        setVideoResult(data);
        toast("数字人视频生成成功");
      } else {
        toast("视频生成失败", "error");
      }
    } catch {
      toast("视频生成失败，请检查网络后重试", "error");
    } finally {
      setVideoLoading(false);
    }
  };

  const currentPlatforms = CONTENT_TYPES.find((ct) => ct.id === contentType)?.platforms ?? [];
  const displayResult = result || (streamScript ? { titles: streamTitles, script: streamScript, tags: [], hook: "" } : null);

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* 左侧：表单 */}
      <Card className="glass-card glow-orange">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Sparkles className="h-5 w-5 text-orange-400" />
            内容生成
          </CardTitle>
          <CardDescription className="text-white/50">输入主题，AI 帮你生成爆款口播内容</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-white/70">主题</label>
            <div className="relative">
              <Input
                placeholder="例如：AI时代普通人如何做自媒体"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onFocus={() => { if (recentTopics.length > 0) setShowTopicDropdown(true); }}
                onBlur={() => setTimeout(() => setShowTopicDropdown(false), 200)}
                className="border-white/10 bg-white/[0.03] text-white placeholder:text-white/30 focus:border-orange-400/50 pr-20"
              />
              {/* Topic action buttons */}
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <button
                  onClick={handlePasteFromClipboard}
                  className="p-1 rounded text-white/30 hover:text-orange-400 hover:bg-white/10 transition-colors"
                  title="从剪贴板粘贴"
                >
                  <ClipboardPaste className="h-3.5 w-3.5" />
                </button>
                {topic && (
                  <>
                    <button
                      onClick={handleClear}
                      className="p-1 rounded text-white/30 hover:text-red-400 hover:bg-white/10 transition-colors"
                      title="清空"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => saveRecentTopic(topic)}
                      className="p-1 rounded text-white/30 hover:text-blue-400 hover:bg-white/10 transition-colors"
                      title="保存到最近使用"
                    >
                      <Clock className="h-3.5 w-3.5" />
                    </button>
                  </>
                )}
              </div>
              {/* Recent topics dropdown */}
              {showTopicDropdown && recentTopics.length > 0 && (
                <div className="absolute right-0 top-full mt-1 z-50 w-64 glass-card border-white/10 rounded-lg shadow-xl overflow-hidden">
                  <div className="px-3 py-1.5 text-[10px] text-white/30 uppercase tracking-wider font-medium border-b border-white/5">
                    最近主题
                  </div>
                  <div className="max-h-48 overflow-y-auto">
                    {recentTopics.map((t, i) => (
                      <button
                        key={i}
                        onClick={() => handleSelectRecentTopic(t)}
                        className="w-full text-left px-3 py-1.5 text-xs text-white/60 hover:bg-white/5 hover:text-white transition-colors truncate"
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white/70">内容类型</label>
            <div className="flex gap-2">
              {CONTENT_TYPES.map((ct) => (
                <Badge key={ct.id} variant={contentType === ct.id ? "default" : "outline"}
                  className={`cursor-pointer ${
                    contentType === ct.id ? "bg-orange-500/80 text-white" : "border-white/15 text-white/50 hover:bg-white/10"
                  }`}
                  onClick={() => { setContentType(ct.id); if (!ct.platforms.includes(platform)) setPlatform(ct.platforms[0]); }}
                >{ct.label}</Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white/70">平台</label>
            <div className="flex flex-wrap gap-2">
              {currentPlatforms.map((p) => (
                <Badge key={p} variant={platform === p ? "default" : "outline"}
                  className={`cursor-pointer text-xs ${
                    platform === p ? "bg-orange-500/80 text-white" : "border-white/15 text-white/50 hover:bg-white/10"
                  }`}
                  onClick={() => setPlatform(p)}
                >{p}</Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white/70">人设</label>
            <div className="flex flex-wrap gap-2">
              {PERSONAS.map((p) => (
                <Badge key={p} variant={persona === p ? "default" : "outline"}
                  className={`cursor-pointer text-xs ${
                    persona === p ? "bg-orange-500/80 text-white" : "border-white/15 text-white/50 hover:bg-white/10"
                  }`}
                  onClick={() => setPersona(p)}
                >{p}</Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white/70">时长: {duration}秒</label>
            <input type="range" min={15} max={300} step={15} value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full accent-orange-500"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white/70">Fire Score 目标</label>
            <div className="flex gap-2">
              {FIRE_SCORE_LEVELS.map((lv) => (
                <Badge key={lv.id} variant={fireScoreLevel === lv.id ? "default" : "outline"}
                  className={`cursor-pointer text-xs ${
                    fireScoreLevel === lv.id ? `${lv.glow} bg-white/10 text-white` : "border-white/15 text-white/40 hover:bg-white/5"
                  }`}
                  onClick={() => setFireScoreLevel(lv.id)}
                >
                  <span className={lv.color}>{lv.label}</span>
                  <span className="ml-1 text-white/30">{lv.desc}</span>
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white/70">封面风格</label>
            <div className="flex gap-2">
              {COVER_STYLES.map((s) => (
                <Badge key={s} variant={coverStyle === s ? "default" : "outline"}
                  className={`cursor-pointer text-xs ${
                    coverStyle === s ? "bg-orange-500/80 text-white" : "border-white/15 text-white/50 hover:bg-white/10"
                  }`}
                  onClick={() => setCoverStyle(s)}
                >{s}</Badge>
              ))}
            </div>
          </div>

          {/* 生成模式切换 */}
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm text-white/50">
              <input
                type="checkbox"
                checked={useStreaming}
                onChange={(e) => setUseStreaming(e.target.checked)}
                className="accent-orange-500"
              />
              流式输出（实时查看生成过程）
            </label>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleGenerate}
              disabled={loading || !topic.trim()}
              className="flex-1 bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600"
            >
              {loading ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />生成中...</>
              ) : (
                <><Sparkles className="mr-2 h-4 w-4" />一键生成</>
              )}
            </Button>
            {loading && (
              <Button
                variant="outline"
                onClick={handleAbort}
                className="border-red-500/50 text-red-400 hover:bg-red-500/10"
              >
                <Pause className="h-4 w-4" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 右侧：结果 */}
      <Card className="glass-card glow-blue">
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-white">
            <span className="flex items-center gap-2">
              生成结果
              {loading && (
                <Badge variant="outline" className="border-orange-500/50 text-orange-400 text-xs animate-pulse">
                  {streamProgress}%
                </Badge>
              )}
            </span>
            {displayResult && (
              <Button variant="ghost" size="sm" onClick={copyScript} className="text-white/50 hover:text-white hover:bg-white/10">
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                {copied ? "已复制" : "复制脚本"}
              </Button>
            )}
          </CardTitle>
          <CardDescription className="text-white/50">
            {loading && streamStatus ? (
              <span className="flex items-center gap-2">
                <Loader2 className="h-3 w-3 animate-spin" />
                {streamStatus}
              </span>
            ) : (
              "填写主题后点击「一键生成」"
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* 实时状态栏 */}
          {loading && (
            <div className="mb-4 space-y-2">
              {/* 进度条 */}
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-orange-500 to-pink-500 transition-all duration-500"
                  style={{ width: `${streamProgress}%` }}
                />
              </div>

              {/* 模型信息 */}
              {streamModel && (
                <div className="flex items-center gap-2 text-xs text-white/40">
                  <Terminal className="h-3 w-3" />
                  <span>模型: {streamModel}</span>
                </div>
              )}
            </div>
          )}

          {displayResult ? (
            <div className="space-y-4">
              {/* 实时标题列表 */}
              <div>
                <h4 className="mb-2 text-sm font-medium text-white/50">
                  推荐标题
                  {loading && streamTitles.length > 0 && (
                    <span className="ml-2 text-xs text-orange-400/60">实时生成中...</span>
                  )}
                </h4>
                <ul className="space-y-1">
                  {(result?.titles || streamTitles).map((t, i) => (
                    <li key={i} className={`text-sm transition-opacity duration-300 ${
                      i < streamTitles.length ? "text-white/70" : "text-white/70"
                    }`}>
                      {i + 1}. {t}
                      {loading && i === streamTitles.length - 1 && (
                        <span className="ml-1 inline-block h-3 w-1 animate-pulse bg-orange-400" />
                      )}
                    </li>
                  ))}
                </ul>
              </div>

              {/* 钩子文案 */}
              {displayResult.hook && (
                <div>
                  <h4 className="mb-2 text-sm font-medium text-white/50">钩子文案</h4>
                  <p className="text-sm font-medium text-orange-400">{displayResult.hook}</p>
                </div>
              )}

              {/* 口播脚本（实时更新） */}
              <div>
                <h4 className="mb-2 text-sm font-medium text-white/50">
                  口播脚本
                  {loading && streamScript.length > 0 && (
                    <span className="ml-2 text-xs text-orange-400/60">写入中...</span>
                  )}
                </h4>
                <div className="relative">
                  <Textarea
                    readOnly
                    value={displayResult.script}
                    className="min-h-[200px] font-mono text-sm border-white/10 bg-white/[0.03] text-white/70"
                  />
                  {loading && streamScript.length > 0 && (
                    <span className="absolute bottom-3 right-3 inline-block h-4 w-1 animate-pulse bg-orange-400" />
                  )}
                </div>
              </div>

              {/* 标签 */}
              {displayResult.tags && displayResult.tags.length > 0 && (
                <div>
                  <h4 className="mb-2 text-sm font-medium text-white/50">标签</h4>
                  <div className="flex flex-wrap gap-2">
                    {(result?.tags || displayResult.tags).map((t, i) => (
                      <Badge key={i} className="border border-white/10 bg-white/5 text-white/60">#{t}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* 生成数字人视频按钮 - 仅在完成后显示 */}
              {!loading && (
                <Button variant="outline" className="w-full border-white/15 text-white/70 hover:bg-white/10"
                  onClick={handleGenerateVideo} disabled={videoLoading}>
                  {videoLoading ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin" />数字人视频生成中...</>) : (<><Video className="mr-2 h-4 w-4" />生成数字人视频</>)}
                </Button>
              )}

              {videoResult && <VideoPreview videoUrl={videoResult.video_url} title={result?.titles?.[0] || streamTitles[0] || ""} />}
            </div>
          ) : (
            <div className="flex h-[400px] items-center justify-center text-white/30">
              <p>填写主题后点击"一键生成"</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
