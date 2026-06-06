"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Sparkles, Copy, Check } from "lucide-react";

const PLATFORMS = ["抖音", "小红书", "B站", "公众号", "YouTube", "TikTok", "快手", "微博", "知乎", "头条", "企鹅号", "大鱼号", "百家号"];
const PERSONAS = ["学长型", "专家型", "闺蜜型", "老铁型", "导师型", "吐槽型", "故事型", "干货型"];

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
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("/api/content/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, platform, persona, duration }),
      });
      const data = await res.json();
      setResult(data);
    } catch (error) {
      console.error(error);
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
            <label className="text-sm font-medium">平台</label>
            <div className="flex flex-wrap gap-2">
              {PLATFORMS.map((p) => (
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
