"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "@/components/toaster";

const tabs = [
  { id: "cold-start", label: "冷启动", glow: "glow-orange" },
  { id: "comments", label: "评论区运营", glow: "glow-blue" },
  { id: "viral", label: "社区裂变", glow: "glow-purple" },
  { id: "publish", label: "发布策略", glow: "glow-green" },
] as const;

type TabId = (typeof tabs)[number]["id"];

const platforms = ["抖音", "小红书", "视频号"];

const summaryCards = [
  { title: "评论区运营", icon: "💬", desc: "引导互动/神评论", glow: "glow-green" },
  { title: "社区裂变", icon: "👥", desc: "私域引流/裂变", glow: "glow-blue" },
  { title: "发布策略", icon: "📅", desc: "黄金时间/频率", glow: "glow-purple" },
];

interface SectionItem {
  text: string;
  bold?: string[]; // words to render as <strong>
}

const SectionList = ({ items }: { items: SectionItem[] }) => (
  <ul className="text-sm text-white/50 space-y-1.5">
    {items.map((item, i) => (
      <li key={i} className="leading-relaxed">
        {item.bold ? (
          <>
            • {item.text.split(/(<\*\*.*?\*\*>)/g).map((part, j) => {
              const match = part.match(/^\*\*(.*?)\*\*$/);
              return match
                ? <strong key={j} className="text-white font-medium">{match[1]}</strong>
                : part;
            })}
          </>
        ) : (
          <>• {item.text}</>
        )}
      </li>
    ))}
  </ul>
);

const sectionData = [
  {
    icon: "💬", title: "神评论引导",
    items: [
      { text: "前3条评论由账号主动发出，引导讨论方向" },
      { text: "设计「争议性」话题引发站队讨论" },
      { text: "用「你呢？」结尾，提高评论率" },
      { text: "评论区置顶补充内容，增加停留时间" },
    ],
  },
  {
    icon: "🤖", title: "自动回复策略",
    items: [
      { text: "关键词触发自动回复（私信引导）" },
      { text: "评论区常见问题FAQ自动回复" },
      { text: "引导关注+收藏的标准回复模板" },
      { text: "负面评论的标准化应对话术" },
    ],
  },
  {
    icon: "📊", title: "数据监控",
    items: [
      { text: "评论率目标：5%以上" },
      { text: "监控负面评论并及时处理" },
      { text: "分析高频关键词优化内容" },
      { text: "跟踪评论转化率（关注/私信）" },
    ],
  },
  {
    icon: "🎯", title: "互动技巧",
    items: [
      { text: "回复前100条评论，提升初始互动率" },
      { text: "用提问句结尾，激发用户表达欲" },
      { text: "制造「信息差」，让用户补充内容" },
      { text: "定期举办评论区抽奖活动" },
    ],
  },
];

const viralData = [
  {
    icon: "🔗", title: "私域引流路径",
    items: [
      { text: "短视频/笔记 → 评论区引导 → 私信自动回复 → 微信/社群" },
      { text: "直播间口播引流，限时福利刺激" },
      { text: "个人主页设置「资料领取」钩子" },
      { text: "跨平台矩阵互相导流" },
    ],
  },
  {
    icon: "🎁", title: "裂变机制设计",
    items: [
      { text: "邀请3人进群，免费领取模板包" },
      { text: "转发朋友圈集赞，解锁高级功能" },
      { text: "组队打卡，互相监督学习" },
      { text: "阶梯奖励：邀请越多，奖励越大" },
    ],
  },
  {
    icon: "👥", title: "社群运营SOP",
    items: [
      { text: "新人入群欢迎+自我介绍引导" },
      { text: "每日固定内容：早报/话题讨论/干货分享" },
      { text: "每周一次直播答疑/连麦" },
      { text: "月度优秀成员评选+奖励" },
    ],
  },
  {
    icon: "📈", title: "增长数据追踪",
    items: [
      { text: "裂变系数 K值 = 邀请人数/参与者" },
      { text: "目标K值 > 1.2（正向裂变）" },
      { text: "监控各渠道ROI，聚焦高效渠道" },
      { text: "社群留存率目标：7日 > 40%" },
    ],
  },
];

const publishData: { icon: string; title: string; items: SectionItem[] }[] = [
  {
    icon: "⏰", title: "黄金发布时间",
    items: [
      { text: "12:00-13:00 / 18:00-20:00 / 21:00-23:00", bold: ["抖音"] },
      { text: "7:00-9:00 / 12:00-14:00 / 18:00-21:00", bold: ["小红书"] },
      { text: "18:00-20:00 / 周末全天", bold: ["B站"] },
      { text: "12:00-13:00 / 19:30-21:30", bold: ["视频号"] },
    ],
  },
  {
    icon: "📅", title: "发布频率建议",
    items: [
      { text: "每天1-2条", bold: ["起步期（0-1万粉）"] },
      { text: "每天1条", bold: ["成长期（1-10万粉）"] },
      { text: "每周3-5条精品", bold: ["稳定期（10万+）"] },
      { text: "每周至少2场，每次1-2小时", bold: ["直播频率"] },
    ],
  },
  {
    icon: "🎯", title: "内容排期策略",
    items: [
      { text: "热点追踪+行业资讯", bold: ["周一"] },
      { text: "干货教程+方法论", bold: ["周二/四"] },
      { text: "案例拆解+对标分析", bold: ["周三"] },
      { text: "互动话题+周末预告", bold: ["周五"] },
      { text: "轻松内容+生活分享", bold: ["周末"] },
    ],
  },
  {
    icon: "🔄", title: "赛马机制",
    items: [
      { text: "同一话题生成3-5个版本同时发布" },
      { text: "24小时后对比数据，保留最优版本" },
      { text: "记录成功模式，复用到后续内容" },
      { text: "A/B测试标题、封面、开头前3秒" },
    ],
  },
];

export default function OperationsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("cold-start");
  const [keyword, setKeyword] = useState("");
  const [platform, setPlatform] = useState("抖音");
  const [generating, setGenerating] = useState(false);

  const handleGenerate = () => {
    if (!keyword.trim()) { toast("请输入赛道关键词", "error"); return; }
    setGenerating(true);
    setTimeout(() => {
      toast(`已为"${keyword}"生成${platform}冷启动方案`, "success");
      setGenerating(false);
    }, 1200);
  };

  const activeGlow = tabs.find((t) => t.id === activeTab)?.glow ?? "glow-orange";

  return (
    <div className="relative">
      {/* 背景光晕 */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute -top-40 right-1/4 h-[500px] w-[500px] rounded-full bg-orange-500/[0.05] blur-[120px]" />
        <div className="absolute bottom-0 left-1/3 h-[400px] w-[400px] rounded-full bg-blue-500/[0.04] blur-[100px]" />
      </div>

      <div className="relative z-10 container py-12 space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <Badge className="border border-orange-500/30 bg-orange-500/10 text-orange-400">冷启动+运营SOP全链路</Badge>
          <h1 className="text-4xl font-bold text-white">运营<span className="text-gradient">中心</span></h1>
          <p className="text-white/50">冷启动方案 + 评论区运营 + 社群裂变 + 发布策略</p>
        </div>

        {/* Tab 导航 */}
        <div className="flex flex-wrap gap-2 justify-center">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`px-5 py-2 text-sm rounded-lg border transition-all duration-200 ${
                activeTab === tab.id
                  ? `border-orange-500/50 bg-orange-500/10 text-orange-400 shadow-glow-orange`
                  : "border-white/10 text-white/40 hover:bg-white/5 hover:text-white/60"
              }`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* 冷启动 */}
        {activeTab === "cold-start" && (
          <div className="space-y-6">
            <Card className={`glass-card ${activeGlow}`}>
              <CardHeader>
                <CardTitle className="text-white">冷启动方案生成</CardTitle>
                <CardDescription className="text-white/50">基于L6保障体系，为你的账号定制30天冷启动方案</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-white/70">赛道关键词</label>
                  <Input
                    placeholder="例如：AI知识分享 / 美妆测评 / 职场干货"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    className="border-white/10 bg-white/[0.03] text-white placeholder:text-white/30 focus:border-orange-400/50"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-white/70">目标平台</label>
                  <div className="flex gap-2">
                    {platforms.map((p) => (
                      <Badge key={p} variant={platform === p ? "default" : "outline"}
                        className={`cursor-pointer ${
                          platform === p ? "bg-orange-500/80 text-white" : "border-white/15 text-white/50 hover:bg-white/10"
                        }`}
                        onClick={() => setPlatform(p)}
                      >{p}</Badge>
                    ))}
                  </div>
                </div>
                <Button onClick={handleGenerate} disabled={generating}
                  className="bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600">
                  {generating ? "生成中..." : "生成冷启动方案"}
                </Button>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {summaryCards.map((item) => (
                <Card key={item.title} className={`glass-card ${item.glow} transition-all duration-300 hover:scale-[1.02]`}>
                  <CardHeader className="py-4">
                    <div className="text-2xl mb-1">{item.icon}</div>
                    <CardTitle className="text-sm text-white">{item.title}</CardTitle>
                    <CardDescription className="text-xs text-white/40">{item.desc}</CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* 评论区运营 */}
        {activeTab === "comments" && (
          <Card className={`glass-card ${activeGlow}`}>
            <CardHeader>
              <CardTitle className="text-white">评论区运营策略</CardTitle>
              <CardDescription className="text-white/50">高效互动，打造高活跃度评论区</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {sectionData.map((section) => (
                  <div key={section.title} className="space-y-2 p-4 rounded-lg border border-white/5 bg-white/[0.02]">
                    <h3 className="font-medium flex items-center gap-2 text-white">
                      <span>{section.icon}</span> {section.title}
                    </h3>
                    <SectionList items={section.items} />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* 社区裂变 */}
        {activeTab === "viral" && (
          <Card className={`glass-card ${activeGlow}`}>
            <CardHeader>
              <CardTitle className="text-white">社区裂变策略</CardTitle>
              <CardDescription className="text-white/50">低成本获取精准用户，实现指数级增长</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {viralData.map((section) => (
                  <div key={section.title} className="space-y-2 p-4 rounded-lg border border-white/5 bg-white/[0.02]">
                    <h3 className="font-medium flex items-center gap-2 text-white">
                      <span>{section.icon}</span> {section.title}
                    </h3>
                    <SectionList items={section.items} />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* 发布策略 */}
        {activeTab === "publish" && (
          <Card className={`glass-card ${activeGlow}`}>
            <CardHeader>
              <CardTitle className="text-white">发布策略</CardTitle>
              <CardDescription className="text-white/50">黄金时间+最优频率，让每条内容都有最大曝光</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {publishData.map((section) => (
                  <div key={section.title} className="space-y-2 p-4 rounded-lg border border-white/5 bg-white/[0.02]">
                    <h3 className="font-medium flex items-center gap-2 text-white">
                      <span>{section.icon}</span> {section.title}
                    </h3>
                    <SectionList items={section.items} />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
