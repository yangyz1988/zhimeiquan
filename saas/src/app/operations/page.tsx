"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "@/components/toaster";

const tabs = [
  { id: "cold-start", label: "冷启动" },
  { id: "comments", label: "评论区运营" },
  { id: "viral", label: "社区裂变" },
  { id: "publish", label: "发布策略" },
] as const;

type TabId = (typeof tabs)[number]["id"];

const platforms = ["抖音", "小红书", "视频号"];

const summaryCards = [
  { title: "评论区运营", icon: "💬", desc: "引导互动/神评论" },
  { title: "社区裂变", icon: "👥", desc: "私域引流/裂变" },
  { title: "发布策略", icon: "📅", desc: "黄金时间/频率" },
];

export default function OperationsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("cold-start");
  const [keyword, setKeyword] = useState("");
  const [platform, setPlatform] = useState("抖音");
  const [generating, setGenerating] = useState(false);

  const handleGenerate = () => {
    if (!keyword.trim()) {
      toast("请输入赛道关键词", "error");
      return;
    }
    setGenerating(true);
    setTimeout(() => {
      toast(`已为"${keyword}"生成${platform}冷启动方案`, "success");
      setGenerating(false);
    }, 1200);
  };

  return (
    <div className="container py-8 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <Badge variant="secondary">冷启动+运营SOP全链路</Badge>
        <h1 className="text-3xl font-bold">运营中心</h1>
        <p className="text-muted-foreground">
          冷启动方案 + 评论区运营 + 社群裂变 + 发布策略
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-2 justify-center">
        {tabs.map((tab) => (
          <Badge
            key={tab.id}
            variant={activeTab === tab.id ? "default" : "outline"}
            className={`cursor-pointer px-4 py-1.5 text-sm transition-colors ${
              activeTab === tab.id
                ? "bg-orange-500 text-white hover:bg-orange-600"
                : "hover:bg-muted"
            }`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </Badge>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "cold-start" && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>冷启动方案生成</CardTitle>
              <CardDescription>
                基于L6保障体系，为你的账号定制30天冷启动方案
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">赛道关键词</label>
                <Input
                  placeholder="例如：AI知识分享 / 美妆测评 / 职场干货"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">目标平台</label>
                <div className="flex gap-2">
                  {platforms.map((p) => (
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
              <Button onClick={handleGenerate} disabled={generating}>
                {generating ? "生成中..." : "生成冷启动方案"}
              </Button>
            </CardContent>
          </Card>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {summaryCards.map((item) => (
              <Card key={item.title}>
                <CardHeader className="py-3">
                  <div className="text-xl mb-1">{item.icon}</div>
                  <CardTitle className="text-sm">{item.title}</CardTitle>
                  <CardDescription className="text-xs">{item.desc}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      )}

      {activeTab === "comments" && (
        <Card>
          <CardHeader>
            <CardTitle>评论区运营策略</CardTitle>
            <CardDescription>高效互动，打造高活跃度评论区</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <span>💬</span> 神评论引导
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1.5">
                  <li>• 前3条评论由账号主动发出，引导讨论方向</li>
                  <li>• 设计「争议性」话题引发站队讨论</li>
                  <li>• 用「你呢？」结尾，提高评论率</li>
                  <li>• 评论区置顶补充内容，增加停留时间</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <span>🤖</span> 自动回复策略
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1.5">
                  <li>• 关键词触发自动回复（私信引导）</li>
                  <li>• 评论区常见问题FAQ自动回复</li>
                  <li>• 引导关注+收藏的标准回复模板</li>
                  <li>• 负面评论的标准化应对话术</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <span>📊</span> 数据监控
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1.5">
                  <li>• 评论率目标：5%以上</li>
                  <li>• 监控负面评论并及时处理</li>
                  <li>• 分析高频关键词优化内容</li>
                  <li>• 跟踪评论转化率（关注/私信）</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <span>🎯</span> 互动技巧
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1.5">
                  <li>• 回复前100条评论，提升初始互动率</li>
                  <li>• 用提问句结尾，激发用户表达欲</li>
                  <li>• 制造「信息差」，让用户补充内容</li>
                  <li>• 定期举办评论区抽奖活动</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "viral" && (
        <Card>
          <CardHeader>
            <CardTitle>社区裂变策略</CardTitle>
            <CardDescription>低成本获取精准用户，实现指数级增长</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <span>🔗</span> 私域引流路径
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1.5">
                  <li>• 短视频/笔记 → 评论区引导 → 私信自动回复 → 微信/社群</li>
                  <li>• 直播间口播引流，限时福利刺激</li>
                  <li>• 个人主页设置「资料领取」钩子</li>
                  <li>• 跨平台矩阵互相导流</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <span>🎁</span> 裂变机制设计
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1.5">
                  <li>• 邀请3人进群，免费领取模板包</li>
                  <li>• 转发朋友圈集赞，解锁高级功能</li>
                  <li>• 组队打卡，互相监督学习</li>
                  <li>• 阶梯奖励：邀请越多，奖励越大</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <span>👥</span> 社群运营SOP
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1.5">
                  <li>• 新人入群欢迎+自我介绍引导</li>
                  <li>• 每日固定内容：早报/话题讨论/干货分享</li>
                  <li>• 每周一次直播答疑/连麦</li>
                  <li>• 月度优秀成员评选+奖励</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <span>📈</span> 增长数据追踪
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1.5">
                  <li>• 裂变系数 K值 = 邀请人数/参与者</li>
                  <li>• 目标K值 &gt; 1.2（正向裂变）</li>
                  <li>• 监控各渠道ROI，聚焦高效渠道</li>
                  <li>• 社群留存率目标：7日 &gt; 40%</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "publish" && (
        <Card>
          <CardHeader>
            <CardTitle>发布策略</CardTitle>
            <CardDescription>黄金时间+最优频率，让每条内容都有最大曝光</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <span>⏰</span> 黄金发布时间
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1.5">
                  <li>• <strong>抖音</strong>：12:00-13:00 / 18:00-20:00 / 21:00-23:00</li>
                  <li>• <strong>小红书</strong>：7:00-9:00 / 12:00-14:00 / 18:00-21:00</li>
                  <li>• <strong>B站</strong>：18:00-20:00 / 周末全天</li>
                  <li>• <strong>视频号</strong>：12:00-13:00 / 19:30-21:30</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <span>📅</span> 发布频率建议
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1.5">
                  <li>• 起步期（0-1万粉）：每天1-2条</li>
                  <li>• 成长期（1-10万粉）：每天1条</li>
                  <li>• 稳定期（10万+）：每周3-5条精品</li>
                  <li>• 直播频率：每周至少2场，每次1-2小时</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <span>🎯</span> 内容排期策略
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1.5">
                  <li>• 周一：热点追踪+行业资讯</li>
                  <li>• 周二/四：干货教程+方法论</li>
                  <li>• 周三：案例拆解+对标分析</li>
                  <li>• 周五：互动话题+周末预告</li>
                  <li>• 周末：轻松内容+生活分享</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h3 className="font-medium flex items-center gap-2">
                  <span>🔄</span> 赛马机制
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1.5">
                  <li>• 同一话题生成3-5个版本同时发布</li>
                  <li>• 24小时后对比数据，保留最优版本</li>
                  <li>• 记录成功模式，复用到后续内容</li>
                  <li>• A/B测试标题、封面、开头前3秒</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
