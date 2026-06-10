"use client";

import { useState } from "react";
import { Check } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/toaster";

const tiers = [
  {
    name: "免费版",
    price: "¥0",
    period: "/永久",
    quota: "3次/天",
    features: ["爆款标题生成", "Fire Score评分", "AI智能配图"],
    buttonLabel: "当前方案",
    variant: "outline" as const,
    disabled: true,
    highlight: false,
    badge: null,
    borderColor: "",
  },
  {
    name: "进阶版",
    price: "¥68",
    period: "/月 (¥568/年)",
    quota: "50次/天",
    features: ["每日50次生成", "对标拆解+自动改写", "违禁词检测", "工单客服"],
    buttonLabel: "立即开通",
    variant: "default" as const,
    disabled: false,
    highlight: true,
    badge: "性价比之王",
    borderColor: "border-orange-500",
  },
  {
    name: "高阶版",
    price: "¥128",
    period: "/月 (¥1,088/年)",
    quota: "150次/天",
    features: ["视频脚本+成片", "数据回流追踪", "优先客服"],
    buttonLabel: "升级高阶版",
    variant: "outline" as const,
    disabled: false,
    highlight: false,
    badge: null,
    borderColor: "",
  },
  {
    name: "旗舰版",
    price: "¥198",
    period: "/月 (¥1,688/年)",
    quota: "无限次",
    features: ["批量/API/多人协作", "自定义品牌模板", "1对1专属客服"],
    buttonLabel: "升级旗舰版",
    variant: "default" as const,
    disabled: false,
    highlight: false,
    badge: "至尊锚点",
    borderColor: "",
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
    <div className="container py-8 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <Badge variant="secondary">限时优惠·首月立减30%</Badge>
        <h1 className="text-3xl font-bold">选择适合你的爆款方案</h1>
        <p className="text-muted-foreground">
          从免费体验到旗舰无限，总有一款适合你
        </p>
      </div>

      {/* Pricing Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {tiers.map((tier) => (
          <Card
            key={tier.name}
            className={`flex flex-col ${
              tier.highlight
                ? "border-2 border-orange-500 scale-105 shadow-lg"
                : ""
            } ${tier.borderColor ? `border-l-4 ${tier.borderColor}` : ""}`}
          >
            <CardHeader className="text-center relative">
              {tier.badge && (
                <Badge
                  className={`absolute -top-2 right-4 text-xs ${
                    tier.badge === "至尊锚点"
                      ? "bg-purple-600 text-white"
                      : "bg-orange-500 text-white"
                  }`}
                >
                  {tier.badge}
                </Badge>
              )}
              <CardTitle className="text-lg">{tier.name}</CardTitle>
              <div className="mt-2">
                <span className="text-3xl font-bold">{tier.price}</span>
                <span className="text-sm text-muted-foreground">
                  {tier.period}
                </span>
              </div>
              <CardDescription className="mt-1 font-medium text-orange-600">
                {tier.quota}
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1">
              <ul className="space-y-2">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-green-500 shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button
                className="w-full"
                variant={tier.variant}
                disabled={tier.disabled || loading !== null}
                onClick={() => handleSelect(tier.name)}
              >
                {loading === tier.name ? "处理中..." : tier.buttonLabel}
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}
