"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Sparkles, Copy, Check, Video } from "lucide-react";
import { toast } from "@/components/toaster";
import { VideoPreview } from "@/components/video-preview";

const CONTENT_TYPES = [
  { id: "text", label: "图文内容", platforms: ["小红书", "微博", "公众号", "知乎", "头条"] },
  { id: "video", label: "视频内容", platforms: ["抖音", "快手", "视频号", "B站", "YouTube", "TikTok"] },
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

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setLoading(true);
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

  const copyScript = () => {
    if (result?.script) {
      navigator.clipboard.writeText(result.script);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleGenerateVideo = async () => {
    if (!result) return;
    setVideoLoading(true);
    try {
      const res = await fetch("/api/video/digital-human", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ script: result.script, title: result.titles[0], platform, persona, duration }),
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
            <Input
              placeholder="例如：AI时代普通人如何做自媒体"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="border-white/10 bg-white/[0.03] text-white placeholder:text-white/30 focus:border-orange-400/50"
            />
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

          <Button onClick={handleGenerate} disabled={loading || !topic.trim()}
            className="w-full bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600">
            {loading ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin" />生成中...</>) : (<><Sparkles className="mr-2 h-4 w-4" />一键生成</>)}
          </Button>
        </CardContent>
      </Card>

      {/* 右侧：结果 */}
      <Card className="glass-card glow-blue">
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-white">
            生成结果
            {result && (
              <Button variant="ghost" size="sm" onClick={copyScript} className="text-white/50 hover:text-white hover:bg-white/10">
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                {copied ? "已复制" : "复制脚本"}
              </Button>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {result ? (
            <div className="space-y-4">
              <div>
                <h4 className="mb-2 text-sm font-medium text-white/50">推荐标题</h4>
                <ul className="space-y-1">
                  {result.titles.map((t, i) => (
                    <li key={i} className="text-sm text-white/70">{i + 1}. {t}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h4 className="mb-2 text-sm font-medium text-white/50">钩子文案</h4>
                <p className="text-sm font-medium text-orange-400">{result.hook}</p>
              </div>

              <div>
                <h4 className="mb-2 text-sm font-medium text-white/50">口播脚本</h4>
                <Textarea readOnly value={result.script}
                  className="min-h-[200px] font-mono text-sm border-white/10 bg-white/[0.03] text-white/70" />
              </div>

              <div>
                <h4 className="mb-2 text-sm font-medium text-white/50">标签</h4>
                <div className="flex flex-wrap gap-2">
                  {result.tags.map((t, i) => (
                    <Badge key={i} className="border border-white/10 bg-white/5 text-white/60">#{t}</Badge>
                  ))}
                </div>
              </div>

              <Button variant="outline" className="w-full border-white/15 text-white/70 hover:bg-white/10"
                onClick={handleGenerateVideo} disabled={videoLoading}>
                {videoLoading ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin" />数字人视频生成中...</>) : (<><Video className="mr-2 h-4 w-4" />生成数字人视频</>)}
              </Button>

              {videoResult && <VideoPreview videoUrl={videoResult.video_url} title={result.titles[0]} />}
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
