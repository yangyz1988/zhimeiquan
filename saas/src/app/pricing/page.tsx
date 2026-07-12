"use client";

import { useState } from "react";
import { Check, Sparkles, Flame, Crown, Zap, Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/toaster";
import { PageBackground } from "@/components/ui/page-layout";

const tiers = [
  {
    name: "免费版", icon: Zap, price: "¥0", period: "/永久", quota: "5次/天 · 3个平台", plan: "free",
    features: [
      "AI 标题生成（抖音/小红书/B站）",
      "Fire Score 基础评分",
      "爆款规则周报（邮件推送）",
      "基础内容模板（3个平台）",
    ],
    buttonLabel: "免费开始", variant: "outline" as const, disabled: false,
    glow: "glow-green", priceColor: "text-green-400",
  },
  {
    name: "进阶版", icon: Sparkles, price: "¥98", period: "/月 (¥798/年)", quota: "50次/天 · 全平台", plan: "basic",
    features: [
      "全13平台 AI 内容生成",
      "爆款规则实时监控 + AI 分析",
      "竞品内容追踪（10个账号）",
      "内容改写引擎",
      "违禁词检测",
      "工单客服",
    ],
    buttonLabel: "立即开通", variant: "default" as const, disabled: false,
    highlight: true, badge: "性价比之王", glow: "glow-orange", priceColor: "text-orange-400",
  },
  {
    name: "高阶版", icon: Flame, price: "¥168", period: "/月 (¥1,388/年)", quota: "150次/天 · 全平台", plan: "pro",
    features: [
      "进阶版全部功能",
      "视频脚本 + 数字人成片",
      "数据回流追踪（Fire Score 校准）",
      "A/B 测试工具",
      "自动化工作流（定时发布）",
      "优先客服",
    ],
    buttonLabel: "升级高阶版", variant: "outline" as const, disabled: false,
    glow: "glow-blue", priceColor: "text-blue-400",
  },
  {
    name: "旗舰版", icon: Crown, price: "¥298", period: "/月 (¥2,488/年)", quota: "无限次 · 全平台", plan: "enterprise",
    features: [
      "高阶版全部功能",
      "无限竞品追踪 + 自动爬取",
      "批量生成 + API 接入",
      "团队协作（5人 + 角色管理）",
      "自定义品牌模板",
      "1对1 专属运营顾问",
    ],
    buttonLabel: "升级旗舰版", variant: "default" as const, disabled: false,
    badge: "企业级", glow: "glow-purple", priceColor: "text-purple-400",
  },
];

export default function PricingPage() {
  const [loading, setLoading] = useState<string | null>(null);

  const handleSubscribe = async (tierName: string, plan: string) => {
    // 免费版：直接跳转到生成页面
    if (plan === "free") {
      window.location.href = "/generate";
      return;
    }

    setLoading(tierName);

    try {
      const res = await fetch("/api/payment/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan }),
      });

      const data = await res.json();

      if (!res.ok) {
        toast(data.error || "创建支付会话失败", "error");
        setLoading(null);
        return;
      }

      if (data.url) {
        // Redirect to Stripe Checkout
        window.location.href = data.url;
      } else {
        toast("未能获取支付链接，请稍后重试", "error");
        setLoading(null);
      }
    } catch (err) {
      toast("网络错误，请检查连接后重试", "error");
      setLoading(null);
    }
  };

  return (
    <div className="relative">
      <PageBackground color1="bg-orange-500/[0.05]" color2="bg-purple-500/[0.05]" />

      <div className="relative z-10 container space-y-12 py-16">
        <div className="text-center space-y-3">
          <Badge className="border border-orange-500/30 bg-orange-500/10 text-orange-400">对标竞品 · 定价更友好</Badge>
          <h1 className="text-4xl font-bold text-white sm:text-5xl">选择适合你的<span className="text-gradient">爆款策略方案</span></h1>
          <p className="text-white/50 max-w-xl mx-auto">介于 AI 写作工具和社媒管理平台之间，覆盖创作全周期</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {tiers.map((tier) => (
            <Card
              key={tier.name}
              className={`glass-card ${tier.glow} flex flex-col transition-all duration-300 ${
                tier.highlight ? "scale-105 shadow-glow-orange z-10" : "hover:scale-[1.02]"
              }`}
            >
              <CardHeader className="text-center relative pb-2">
                {tier.badge && (
                  <Badge className={`absolute -top-2 right-4 text-xs ${
                    tier.badge === "至尊锚点"
                      ? "bg-gradient-to-r from-purple-600 to-pink-600 text-white"
                      : "bg-gradient-to-r from-orange-500 to-red-500 text-white"
                  }`}>
                    {tier.badge}
                  </Badge>
                )}
                <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-white/5">
                  <tier.icon className={`h-5 w-5 ${tier.priceColor}`} />
                </div>
                <CardTitle className="text-lg text-white">{tier.name}</CardTitle>
                <div className="mt-2">
                  <span className={`text-3xl font-bold ${tier.priceColor}`}>{tier.price}</span>
                  <span className="text-sm text-white/40">{tier.period}</span>
                </div>
                <CardDescription className={`mt-1 font-medium ${tier.priceColor}`}>
                  {tier.quota}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 pt-4">
                <ul className="space-y-3">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-sm text-white/60">
                      <div className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-green-500/20">
                        <Check className="h-2.5 w-2.5 text-green-400" />
                      </div>
                      {feature}
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter className="pt-2">
                <Button
                  className={`w-full ${
                    tier.highlight
                      ? "bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600"
                      : tier.disabled ? "border-white/10 text-white/30" : "border-white/15 bg-white/5 text-white/70 hover:bg-white/10"
                  }`}
                  variant={tier.disabled ? "outline" : tier.variant}
                  disabled={tier.disabled || loading !== null}
                  onClick={() => handleSubscribe(tier.name, tier.plan)}
                >
                  {loading === tier.name ? (
                    <span className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      处理中...
                    </span>
                  ) : (
                    tier.buttonLabel
                  )}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        <div className="text-center text-sm text-white/30 space-y-1">
          <p>所有付费方案均支持 7 天无理由退款</p>
          <p>定价参考：AI 写作工具 $20-50/月 · 社媒管理 $100-250/月 · 智媒圈 ¥98-298/月（功能覆盖两者）</p>
        </div>
      </div>
    </div>
  );
}
