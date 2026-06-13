"use client";

import { useState } from "react";
import { Check, Sparkles, Flame, Crown, Zap } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/toaster";
import { PageBackground } from "@/components/ui/page-layout";

const tiers = [
  {
    name: "免费版", icon: Zap, price: "¥0", period: "/永久", quota: "3次/天",
    features: ["爆款标题生成", "Fire Score评分", "AI智能配图"],
    buttonLabel: "当前方案", variant: "outline" as const, disabled: true,
    glow: "glow-green", priceColor: "text-green-400",
  },
  {
    name: "进阶版", icon: Sparkles, price: "¥68", period: "/月 (¥568/年)", quota: "50次/天",
    features: ["每日50次生成", "对标拆解+自动改写", "违禁词检测", "工单客服"],
    buttonLabel: "立即开通", variant: "default" as const, disabled: false,
    highlight: true, badge: "性价比之王", glow: "glow-orange", priceColor: "text-orange-400",
  },
  {
    name: "高阶版", icon: Flame, price: "¥128", period: "/月 (¥1,088/年)", quota: "150次/天",
    features: ["视频脚本+成片", "数据回流追踪", "优先客服"],
    buttonLabel: "升级高阶版", variant: "outline" as const, disabled: false,
    glow: "glow-blue", priceColor: "text-blue-400",
  },
  {
    name: "旗舰版", icon: Crown, price: "¥198", period: "/月 (¥1,688/年)", quota: "无限次",
    features: ["批量/API/多人协作", "自定义品牌模板", "1对1专属客服"],
    buttonLabel: "升级旗舰版", variant: "default" as const, disabled: false,
    badge: "至尊锚点", glow: "glow-purple", priceColor: "text-purple-400",
  },
];

export default function PricingPage() {
  const [loading, setLoading] = useState<string | null>(null);

  const handleSelect = (tierName: string) => {
    if (tierName === "免费版") return;
    setLoading(tierName);
    setTimeout(() => {
      toast(`${tierName}开通功能即将上线，敬请期待`, "success");
      setLoading(null);
    }, 1000);
  };

  return (
    <div className="relative">
      <PageBackground color1="bg-orange-500/[0.05]" color2="bg-purple-500/[0.05]" />

      <div className="relative z-10 container space-y-12 py-16">
        <div className="text-center space-y-3">
          <Badge className="border border-orange-500/30 bg-orange-500/10 text-orange-400">限时优惠·首月立减30%</Badge>
          <h1 className="text-4xl font-bold text-white sm:text-5xl">选择适合你的<span className="text-gradient">爆款方案</span></h1>
          <p className="text-white/50 max-w-xl mx-auto">从免费体验到旗舰无限，总有一款适合你</p>
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
                  onClick={() => handleSelect(tier.name)}
                >
                  {loading === tier.name ? "处理中..." : tier.buttonLabel}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        <div className="text-center text-sm text-white/30 space-y-1">
          <p>所有付费方案均支持 7 天无理由退款</p>
          <p>如有疑问，请联系客服微信：zhimeiquan_ai</p>
        </div>
      </div>
    </div>
  );
}
