"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageBackground } from "@/components/ui/page-layout";
import {
  TrendingUp, Clock, Target, ArrowRight, Download, Mail,
  ChevronRight, Sparkles, BarChart3, Flame,
} from "lucide-react";
import { toast } from "@/components/toaster";

/* ------------------------------------------------------------------ */
/* 平台颜色映射                                                           */
/* ------------------------------------------------------------------ */

const PLATFORM_COLORS: Record<string, string> = {
  "抖音": "bg-pink-500/10 text-pink-400 border-pink-500/30",
  "小红书": "bg-red-500/10 text-red-400 border-red-500/30",
  "B站": "bg-blue-500/10 text-blue-400 border-blue-500/30",
  "微博": "bg-orange-500/10 text-orange-400 border-orange-500/30",
  "知乎": "bg-sky-500/10 text-sky-400 border-sky-500/30",
  "头条": "bg-red-500/10 text-red-400 border-red-500/30",
  "快手": "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  "YouTube": "bg-red-600/10 text-red-500 border-red-600/30",
  "TikTok": "bg-gray-400/10 text-gray-300 border-gray-400/30",
  "公众号": "bg-green-500/10 text-green-400 border-green-500/30",
  "视频号": "bg-green-500/10 text-green-400 border-green-500/30",
  "百度热搜": "bg-blue-500/10 text-blue-400 border-blue-500/30",
  "Instagram": "bg-purple-500/10 text-purple-400 border-purple-500/30",
};

/* ------------------------------------------------------------------ */
/* Mock 报告数据（API 未连接时展示）                                       */
/* ------------------------------------------------------------------ */

const MOCK_REPORTS = [
  {
    platform: "抖音",
    summary: "6种高CTR标题模式，完播率>45%是核心指标，反常识型和好奇心缺口型标题CTR最高",
    core_metric: "完播率",
    hot_topics: ["职场生存指南", "副业赚钱", "AI工具推荐", "个人成长", "生活小技巧"],
    best_posting: "推荐在 18:00-20:00 发布（下班黄金档）",
  },
  {
    platform: "小红书",
    summary: "痛点解决方案型和干货清单型标题效果最好，收藏率是核心权重（高于点赞率2-3倍）",
    core_metric: "收藏率",
    hot_topics: ["平价好物", "护肤心得", "穿搭公式", "减脂餐食谱", "家居改造"],
    best_posting: "推荐在 20:00-22:00 发布（晚间浏览高峰）",
  },
  {
    platform: "B站",
    summary: "硬核干货和测评类内容最受欢迎，三连率>8%触发强推荐，弹幕互动密度是社区文化指标",
    core_metric: "三连率",
    hot_topics: ["数码评测", "学习干货", "游戏实况", "科普解说", "美食教程"],
    best_posting: "推荐在 20:00-23:00 发布（晚间黄金档）",
  },
  {
    platform: "微博",
    summary: "热搜话题+情绪共鸣型内容传播力最强，带话题词的微博互动量高出普通微博2.5倍",
    core_metric: "转发量",
    hot_topics: ["社会热点", "明星动态", "剧集吐槽", "情感话题", "节日营销"],
    best_posting: "推荐在 08:00-10:00 和 20:00-23:00 发布（早晚双高峰）",
  },
  {
    platform: "头条",
    summary: "标题决定80%的点击率，三段式叙事结构推荐量最高，民生类和反差类内容打开率领先",
    core_metric: "推荐量",
    hot_topics: ["社会民生", "国际局势", "历史故事", "三农资讯", "汽车评测"],
    best_posting: "推荐在 07:00-09:00 发布（早间资讯阅读高峰）",
  },
  {
    platform: "快手",
    summary: "高互动率（评论+分享）是核心权重，人设感和真实感内容完播率远超精致制作",
    core_metric: "互动率",
    hot_topics: ["农村生活", "手艺达人", "美食制作", "搞笑段子", "才艺展示"],
    best_posting: "推荐在 17:00-21:00 发布（傍晚休闲黄金档）",
  },
  {
    platform: "知乎",
    summary: "深度长文和反直觉科普型回答收藏率最高，收藏/赞比>0.8进入高权重池",
    core_metric: "赞同数",
    hot_topics: ["行业分析", "职业规划", "学习方法", "投资理财", "科技趋势"],
    best_posting: "推荐在 20:00-22:00 发布（晚间深度阅读时段）",
  },
  {
    platform: "公众号",
    summary: "分享率是第一传播指标，开头3秒定生死，强共鸣+强信息差型文章打开率高",
    core_metric: "分享率",
    hot_topics: ["职场干货", "认知提升", "财经分析", "教育话题", "健康养生"],
    best_posting: "推荐在 07:00-08:30 和 21:00-22:30 发布（早晚阅读高峰）",
  },
  {
    platform: "视频号",
    summary: "社交裂变是核心分发逻辑，好友互动（点赞/收藏）权重最高，正能量内容自然流量大",
    core_metric: "好友互动量",
    hot_topics: ["新闻时事", "生活记录", "音乐表演", "知识分享", "正能量故事"],
    best_posting: "推荐在 12:00-14:00 和 19:00-21:00 发布（午休+晚间社交活跃期）",
  },
  {
    platform: "百度热搜",
    summary: "搜索意图精准匹配是流量密码，长尾词+热点结合的策略搜索曝光量最高",
    core_metric: "搜索指数",
    hot_topics: ["实时热点", "娱乐八卦", "政策解读", "健康科普", "天气灾害"],
    best_posting: "推荐在热点发生后 1-2 小时内发布（抢占搜索窗口期）",
  },
  {
    platform: "YouTube",
    summary: "前30秒观众留存率决定算法推荐力度，系列化内容和教程类视频长期流量最稳定",
    core_metric: "观众留存率",
    hot_topics: ["科技评测", "教程教学", "Vlog生活", "音乐MV", "纪录片"],
    best_posting: "推荐在 14:00-16:00 EST 发布（北美黄金档）",
  },
  {
    platform: "TikTok",
    summary: "前3秒留存>65%触发推荐池扩容，loop率（重复播放率）是新晋核心指标",
    core_metric: "完播率",
    hot_topics: ["舞蹈挑战", "转场特效", "生活黑客", "宠物萌宠", "美食短视频"],
    best_posting: "推荐在 07:00-09:00 和 19:00-21:00 发布（通勤+晚间休闲时段）",
  },
  {
    platform: "Instagram",
    summary: "Reels视频优先级最高，视觉一致性强的账号粉丝增长快3倍，Carousel帖子保存率最高",
    core_metric: "互动率",
    hot_topics: ["旅行摄影", "时尚穿搭", "美食摆拍", "健身塑形", "极简生活"],
    best_posting: "推荐在 11:00-13:00 和 19:00-21:00 发布（午餐+晚间浏览高峰）",
  },
];

const ALL_PLATFORMS = [
  "抖音", "小红书", "B站", "微博", "知乎", "头条", "快手",
  "YouTube", "TikTok", "公众号", "视频号", "百度热搜", "Instagram",
];

/* ------------------------------------------------------------------ */
/* 页面组件                                                              */
/* ------------------------------------------------------------------ */

export default function ReportsPage() {
  const [reports, setReports] = useState(MOCK_REPORTS);
  const [email, setEmail] = useState("");
  const [subscribing, setSubscribing] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);

  useEffect(() => {
    // 尝试从后端加载报告
    fetch("/api/insights/reports")
      .then((res) => res.json())
      .then((data) => {
        if (data.reports && data.reports.length > 0) {
          setReports(data.reports);
        }
      })
      .catch(() => {
        // API 不可用时使用 mock 数据
      });
  }, []);

  const handleSubscribe = async () => {
    if (!email || !email.includes("@")) {
      toast("请输入有效邮箱地址", "error");
      return;
    }
    setSubscribing(true);
    try {
      await fetch("/api/insights/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      toast("订阅成功！每周将收到最新爆款规则报告", "success");
      setEmail("");
    } catch {
      toast("订阅失败，请稍后再试", "error");
    } finally {
      setSubscribing(false);
    }
  };

  return (
    <div className="relative">
      <PageBackground color1="bg-orange-500/[0.05]" color2="bg-blue-500/[0.05]" />

      <div className="relative z-10 container space-y-12 py-16">
        {/* ---- Hero ---- */}
        <div className="text-center space-y-4">
          <Badge className="border border-orange-500/30 bg-orange-500/10 text-orange-400">
            免费开放 · 每周更新
          </Badge>
          <h1 className="text-4xl font-bold text-white sm:text-5xl">
            平台爆款规则<span className="text-gradient">分析报告</span>
          </h1>
          <p className="text-white/50 max-w-2xl mx-auto text-lg">
            基于实时采集的各平台热门数据 + AI 分析，告诉你每个平台现在什么最火、怎么写更容易爆。
            不是玄学，是数据。
          </p>

          {/* 邮件订阅 */}
          <div className="flex flex-col sm:flex-row justify-center gap-3 pt-4 max-w-md mx-auto sm:max-w-none">
            <div className="relative flex-1">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30" />
              <Input
                type="email"
                placeholder="输入邮箱，订阅每周爆款报告"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-10 border-white/10 bg-white/5 text-white placeholder:text-white/30"
              />
            </div>
            <Button
              onClick={handleSubscribe}
              disabled={subscribing}
              className="bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600 shrink-0"
            >
              {subscribing ? "订阅中..." : "免费订阅"}
              <Download className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* ---- 报告卡片 ---- */}
        <div>
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-orange-400" />
            最新平台报告
            <Badge className="border border-orange-500/30 bg-orange-500/10 text-orange-400 text-xs">
              共 {ALL_PLATFORMS.length} 个平台
            </Badge>
          </h2>
          <div className="grid gap-6 md:grid-cols-2">
            {reports.map((report) => (
              <Card
                key={report.platform}
                className={`glass-card glow-orange cursor-pointer transition-all duration-300 hover:scale-[1.01] ${
                  selectedPlatform === report.platform ? "ring-2 ring-orange-500/50" : ""
                }`}
                onClick={() =>
                  setSelectedPlatform(
                    selectedPlatform === report.platform ? null : report.platform
                  )
                }
              >
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Badge className={PLATFORM_COLORS[report.platform] || "border-white/10"}>
                        {report.platform}
                      </Badge>
                      <CardTitle className="text-white text-lg">
                        {report.platform}爆款规则
                      </CardTitle>
                    </div>
                    <ChevronRight
                      className={`h-4 w-4 text-white/30 transition-transform ${
                        selectedPlatform === report.platform ? "rotate-90" : ""
                      }`}
                    />
                  </div>
                  <CardDescription className="text-white/50 pt-2">
                    {report.summary}
                  </CardDescription>
                </CardHeader>

                {selectedPlatform === report.platform && (
                  <CardContent className="space-y-4 border-t border-white/5 pt-4">
                    {/* 核心指标 */}
                    <div className="flex items-center gap-2">
                      <Target className="h-4 w-4 text-orange-400" />
                      <span className="text-sm text-white/60">核心指标：</span>
                      <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/30">
                        {report.core_metric}
                      </Badge>
                    </div>

                    {/* 热门话题 */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Flame className="h-4 w-4 text-red-400" />
                        <span className="text-sm text-white/60">当前热门话题</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {report.hot_topics.map((topic) => (
                          <Badge key={topic} className="border border-white/10 bg-white/5 text-white/60">
                            {topic}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* 最佳发布时间 */}
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-blue-400" />
                      <span className="text-sm text-white/60">{report.best_posting}</span>
                    </div>

                    {/* CTA */}
                    <div className="flex gap-3 pt-2">
                      <Link href="/generate">
                        <Button size="sm" className="bg-gradient-to-r from-orange-500 to-pink-500">
                          用规则生成内容
                          <Sparkles className="ml-1 h-3 w-3" />
                        </Button>
                      </Link>
                      <Link href="/monitor">
                        <Button size="sm" variant="outline" className="border-white/15 text-white/60 hover:bg-white/10">
                          查看完整监控
                        </Button>
                      </Link>
                    </div>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        </div>

        {/* ---- 底部 CTA ---- */}
        <section className="text-center space-y-6 py-12">
          <div className="flex items-center justify-center gap-2">
            <BarChart3 className="h-5 w-5 text-orange-400" />
            <h2 className="text-2xl font-bold text-white">不只是看报告，用规则做爆款</h2>
          </div>
          <p className="text-white/40 max-w-lg mx-auto">
            报告里的每条规则都可以直接用于内容生成——选择平台，输入主题，
            AI 自动匹配爆款标题公式和钩子类型
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link href="/generate">
              <Button size="lg" className="w-full sm:w-auto bg-gradient-to-r from-orange-500 to-pink-500">
                免费试试
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/pricing">
              <Button variant="outline" size="lg" className="w-full sm:w-auto border-white/15 text-white/70">
                查看定价
              </Button>
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
