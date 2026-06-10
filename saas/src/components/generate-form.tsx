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

const PLATFORMS = ["抖音", "小红书", "B站", "公众号", "YouTube", "TikTok", "快手", "微博", "知乎", "头条", "企鹅号", "大鱼号", "百家号"];
const PERSONAS = ["学长型", "专家型", "闺蜜型", "老铁型", "导师型", "吐槽型", "故事型", "干货型"];
const CONTENT_TYPES = [
  { id: "text", label: "图文内容", platforms: ["小红书", "微博", "公众号", "知乎", "头条"] },
  { id: "video", label: "视频内容", platforms: ["抖音", "快手", "视频号", "B站", "YouTube", "TikTok"] },
];
const FIRE_SCORE_LEVELS = [
  { id: "lv4", label: "Lv4 通杀", desc: "70+", color: "text-blue-500" },
  { id: "lv3", label: "Lv3 小爆", desc: "80+", color: "text-green-500" },
  { id: "lv2", label: "Lv2 大爆", desc: "90+", color: "text-orange-500" },
  { id: "lv1", label: "Lv1 爆款", desc: "95+", color: "text-red-500" },
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
  const [videoResult, setVideoResult] = useState<{ video_url: string } | null>(
    null,
  );

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
    } catch (error) {
      console.error(error);
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
        body: JSON.stringify({
          script: result.script,
          title: result.titles[0],
          platform,
          persona,
          duration,
        }),
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

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-orange-500" />
            内容生成
          </CardTitle>
          <CardDescription>输入主题，AI 帮你生成爆款口播内容</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">主题</label>
            <Input
              placeholder="例如：AI时代普通人如何做自媒体"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">内容类型</label>
            <div className="flex gap-2">
              {CONTENT_TYPES.map((ct) => (
                <Badge
                  key={ct.id}
                  variant={contentType === ct.id ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => {
                    setContentType(ct.id);
                    if (!ct.platforms.includes(platform)) {
                      setPlatform(ct.platforms[0]);
                    }
                  }}
                >
                  {ct.label}
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">平台</label>
            <div className="flex flex-wrap gap-2">
              {CONTENT_TYPES
                .find((ct) => ct.id === contentType)
                ?.platforms.map((p) => (
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
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">人设</label>
            <div className="flex flex-wrap gap-2">
              {PERSONAS.map((p) => (
                <Badge
                  key={p}
                  variant={persona === p ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => setPersona(p)}
                >
                  {p}
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">时长: {duration}秒</label>
            <input
              type="range"
              min={15}
              max={300}
              step={15}
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Fire Score 目标</label>
            <div className="flex gap-2">
              {FIRE_SCORE_LEVELS.map((lv) => (
                <Badge
                  key={lv.id}
                  variant={fireScoreLevel === lv.id ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => setFireScoreLevel(lv.id)}
                >
                  <span className={lv.color}>{lv.label}</span>
                  <span className="ml-1 text-xs text-muted-foreground">{lv.desc}</span>
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">封面风格</label>
            <div className="flex gap-2">
              {COVER_STYLES.map((s) => (
                <Badge
                  key={s}
                  variant={coverStyle === s ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => setCoverStyle(s)}
                >
                  {s}
                </Badge>
              ))}
            </div>
          </div>

          <Button onClick={handleGenerate} disabled={loading || !topic.trim()} className="w-full">
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                生成中...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                一键生成
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            生成结果
            {result && (
              <Button variant="ghost" size="sm" onClick={copyScript}>
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
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">推荐标题</h4>
                <ul className="space-y-1">
                  {result.titles.map((t, i) => (
                    <li key={i} className="text-sm">{i + 1}. {t}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">钩子文案</h4>
                <p className="text-sm font-medium text-orange-500">{result.hook}</p>
              </div>

              <div>
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">口播脚本</h4>
                <Textarea readOnly value={result.script} className="min-h-[200px] font-mono text-sm" />
              </div>

              <div>
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">标签</h4>
                <div className="flex flex-wrap gap-2">
                  {result.tags.map((t, i) => (
                    <Badge key={i} variant="secondary">#{t}</Badge>
                  ))}
                </div>
              </div>

              <Button
                variant="outline"
                className="w-full"
                onClick={handleGenerateVideo}
                disabled={videoLoading}
              >
                {videoLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    数字人视频生成中...
                  </>
                ) : (
                  <>
                    <Video className="mr-2 h-4 w-4" />
                    生成数字人视频
                  </>
                )}
              </Button>

              {videoResult && (
                <VideoPreview
                  videoUrl={videoResult.video_url}
                  title={result.titles[0]}
                />
              )}
            </div>
          ) : (
            <div className="flex h-[400px] items-center justify-center text-muted-foreground">
              <p>填写主题后点击"一键生成"</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
