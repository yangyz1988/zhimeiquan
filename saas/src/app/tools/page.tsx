"use client";

import { useState } from "react";
import { Sparkles, Flame } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/toaster";

const platforms = ["抖音", "小红书", "B站"];
const counts = ["5", "10", "20"];
const styles = ["悬念式", "数字式", "痛点式", "反常识", "对比式", "故事式"];

export default function ToolsPage() {
  const [topic, setTopic] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState("抖音");
  const [selectedCount, setSelectedCount] = useState("10");
  const [selectedStyles, setSelectedStyles] = useState<string[]>(["悬念式"]);
  const [generating, setGenerating] = useState(false);
  const [titleResults, setTitleResults] = useState<string[]>([]);

  const [scoreContent, setScoreContent] = useState("");
  const [scorePlatform, setScorePlatform] = useState("抖音");
  const [scoring, setScoring] = useState(false);
  const [scoreResult, setScoreResult] = useState<{
    total: number;
    dimensions: { name: string; score: number }[];
  } | null>(null);

  const toggleStyle = (style: string) => {
    setSelectedStyles((prev) =>
      prev.includes(style) ? prev.filter((s) => s !== style) : [...prev, style]
    );
  };

  const handleGenerate = () => {
    if (!topic.trim()) { toast("请输入话题", "error"); return; }
    setGenerating(true);
    fetch("/api/titles/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, platform: selectedPlatform, count: Number(selectedCount), style: selectedStyles }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (data.titles) {
          setTitleResults(data.titles);
          toast("标题生成成功", "success");
        } else {
          const demo = Array.from({ length: Number(selectedCount) }, (_, i) => `【${selectedStyles[0] ?? "悬念式"}】${topic}的${i + 1}个爆款标题`);
          setTitleResults(demo);
          toast("已生成演示标题（API未连接）", "success");
        }
      })
      .catch(() => {
        const demo = Array.from({ length: Number(selectedCount) }, (_, i) => `【${selectedStyles[0] ?? "悬念式"}】${topic}的${i + 1}个爆款标题`);
        setTitleResults(demo);
        toast("已生成演示标题（API未连接）", "success");
      })
      .finally(() => setGenerating(false));
  };

  const handleScore = () => {
    if (!scoreContent.trim()) { toast("请输入标题或内容", "error"); return; }
    setScoring(true);
    fetch("/api/content/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: scoreContent, platform: scorePlatform }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (data.total) {
          setScoreResult(data);
          toast("评分完成", "success");
        } else {
          setScoreResult({
            total: 82,
            dimensions: [
              { name: "吸引力", score: 85 }, { name: "情绪共鸣", score: 78 },
              { name: "信息密度", score: 80 }, { name: "传播性", score: 88 }, { name: "转化力", score: 79 },
            ],
          });
          toast("已生成演示评分（API未连接）", "success");
        }
      })
      .catch(() => {
        setScoreResult({
          total: 82,
          dimensions: [
            { name: "吸引力", score: 85 }, { name: "情绪共鸣", score: 78 },
            { name: "信息密度", score: 80 }, { name: "传播性", score: 88 }, { name: "转化力", score: 79 },
          ],
        });
        toast("已生成演示评分（API未连接）", "success");
      })
      .finally(() => setScoring(false));
  };

  return (
    <div className="relative">
      {/* 背景光晕 */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute -top-40 left-1/4 h-[500px] w-[500px] rounded-full bg-orange-500/[0.05] blur-[120px]" />
        <div className="absolute bottom-20 right-1/4 h-[400px] w-[400px] rounded-full bg-blue-500/[0.05] blur-[100px]" />
      </div>

      <div className="relative z-10 container py-12 space-y-10">
        {/* Header */}
        <div className="text-center space-y-3">
          <Badge className="border border-orange-500/30 bg-orange-500/10 text-orange-400">爆款文案+评分双引擎</Badge>
          <h1 className="text-4xl font-bold text-white">爆款<span className="text-gradient">工具箱</span></h1>
          <p className="text-white/50">标题生成 · Fire Score评分 · 违禁词检测 · 一键优化</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左侧：标题生成器 */}
          <Card className="glass-card glow-orange">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Sparkles className="h-5 w-5 text-orange-400" />
                爆款标题生成器
              </CardTitle>
              <CardDescription className="text-white/50">输入话题，AI生成多个爆款标题</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-white/70">话题</label>
                <Input
                  placeholder="例如：AI副业 / 职场潜规则"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  className="border-white/10 bg-white/[0.03] text-white placeholder:text-white/30 focus:border-orange-400/50"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-white/70">平台</label>
                  <div className="flex gap-1.5">
                    {platforms.map((p) => (
                      <Badge key={p} variant={selectedPlatform === p ? "default" : "outline"}
                        className={`cursor-pointer text-xs ${
                          selectedPlatform === p ? "bg-orange-500/80 text-white" : "border-white/15 text-white/50 hover:bg-white/10"
                        }`}
                        onClick={() => setSelectedPlatform(p)}
                      >{p}</Badge>
                    ))}
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-white/70">数量</label>
                  <div className="flex gap-1.5">
                    {counts.map((c) => (
                      <Badge key={c} variant={selectedCount === c ? "default" : "outline"}
                        className={`cursor-pointer text-xs ${
                          selectedCount === c ? "bg-orange-500/80 text-white" : "border-white/15 text-white/50 hover:bg-white/10"
                        }`}
                        onClick={() => setSelectedCount(c)}
                      >{c}个</Badge>
                    ))}
                  </div>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-white/70">风格</label>
                <div className="flex flex-wrap gap-1.5">
                  {styles.map((s) => (
                    <Badge key={s} variant={selectedStyles.includes(s) ? "default" : "outline"}
                      className={`cursor-pointer text-xs ${
                        selectedStyles.includes(s) ? "bg-orange-500/80 text-white" : "border-white/15 text-white/50 hover:bg-white/10"
                      }`}
                      onClick={() => toggleStyle(s)}
                    >{s}</Badge>
                  ))}
                </div>
              </div>

              <Button onClick={handleGenerate} disabled={generating}
                className="w-full bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600">
                {generating ? "生成中..." : "生成爆款标题"}
              </Button>

              {titleResults.length > 0 && (
                <div className="space-y-2 mt-2">
                  <p className="text-sm font-medium text-white/50">生成结果（{titleResults.length}个）</p>
                  <ul className="space-y-1.5">
                    {titleResults.map((title, i) => (
                      <li key={i} className="text-sm rounded-md border border-white/5 bg-white/[0.03] px-3 py-2 text-white/70 hover:bg-white/[0.06] transition-colors">
                        {title}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 右侧：Fire Score */}
          <Card className="glass-card glow-blue">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Flame className="h-5 w-5 text-blue-400" />
                Fire Score 2.0 评分
              </CardTitle>
              <CardDescription className="text-white/50">五维度综合评分，精准定位优化方向</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-white/70">标题或内容</label>
                <Textarea
                  placeholder="粘贴你的标题或内容，系统将进行五维度评分..."
                  value={scoreContent}
                  onChange={(e) => setScoreContent(e.target.value)}
                  rows={5}
                  className="border-white/10 bg-white/[0.03] text-white placeholder:text-white/30 focus:border-blue-400/50"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-white/70">目标平台</label>
                <div className="flex gap-2">
                  <Badge variant={scorePlatform === "抖音" ? "default" : "outline"}
                    className={`cursor-pointer ${
                      scorePlatform === "抖音" ? "bg-blue-500/80 text-white" : "border-white/15 text-white/50 hover:bg-white/10"
                    }`}
                    onClick={() => setScorePlatform("抖音")}
                  >抖音(完播率导向)</Badge>
                  <Badge variant={scorePlatform === "小红书" ? "default" : "outline"}
                    className={`cursor-pointer ${
                      scorePlatform === "小红书" ? "bg-blue-500/80 text-white" : "border-white/15 text-white/50 hover:bg-white/10"
                    }`}
                    onClick={() => setScorePlatform("小红书")}
                  >小红书(收藏率导向)</Badge>
                </div>
              </div>

              <Button onClick={handleScore} disabled={scoring}
                className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600">
                {scoring ? "评分中..." : "开始评分"}
              </Button>

              {scoreResult && (
                <div className="space-y-3 mt-2">
                  <div className="text-center">
                    <span className="text-4xl font-bold text-gradient-blue">{scoreResult.total}</span>
                    <span className="text-sm text-white/40 ml-1">/100</span>
                  </div>
                  <div className="space-y-2">
                    {scoreResult.dimensions.map((dim) => (
                      <div key={dim.name} className="flex items-center gap-2">
                        <span className="text-sm w-20 shrink-0 text-white/60">{dim.name}</span>
                        <div className="flex-1 rounded-full bg-white/[0.06] h-2.5 overflow-hidden">
                          <div className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-700"
                            style={{ width: `${dim.score}%` }} />
                        </div>
                        <span className="text-sm text-white/40 w-8 text-right">{dim.score}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
