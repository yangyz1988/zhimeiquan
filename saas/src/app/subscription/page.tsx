"use client";

import { useState, useEffect } from "react";
import { CreditCard, Crown, Check, Zap, Building } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/components/toaster";
import { apiFetch } from "@/lib/api";

interface Subscription {
  id: string;
  plan: string;
  status: string;
  current_period_end?: string;
  cancel_at_period_end: boolean;
  features?: { credits: number; api_calls: number; storage_gb: number };
}

const plans = [
  { id: "FREE", name: "免费版", price: 0, features: ["100 积分/月", "1000 API 调用", "1GB 存储", "基础功能"] },
  { id: "PRO", name: "专业版", price: 99, features: ["1000 积分/月", "10000 API 调用", "10GB 存储", "高级分析", "优先支持"] },
  { id: "TEAM", name: "团队版", price: 299, features: ["5000 积分/月", "50000 API 调用", "50GB 存储", "团队协作", "专属客服"] },
  { id: "ENTERPRISE", name: "企业版", price: 999, features: ["无限积分", "无限 API", "500GB 存储", "私有部署", "SLA 保障"] },
];

export default function SubscriptionPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSubscription();
  }, []);

  const loadSubscription = async () => {
    setLoading(true);
    try {
      const result = await apiFetch<Subscription>("/api/subscriptions");
      if (result.ok && result.data) setSubscription(result.data);
    } catch {
      setSubscription({ id: "demo", plan: "FREE", status: "ACTIVE", cancel_at_period_end: false });
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (planId: string) => {
    try {
      const result = await apiFetch("/api/subscriptions", {
        method: "POST",
        body: { plan: planId },
      });
      if (result.ok) {
        toast(`已升级到 ${planId}`, "success");
        loadSubscription();
      }
    } catch {
      toast("升级失败", "error");
    }
  };

  const handleCancel = async () => {
    try {
      const result = await apiFetch("/api/subscriptions", {
        method: "POST",
        body: { action: "cancel" },
      });
      if (result.ok) {
        toast("已取消自动续费", "success");
        loadSubscription();
      }
    } catch {
      toast("操作失败", "error");
    }
  };

  const currentPlan = plans.find(p => p.id === subscription?.plan) || plans[0];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">订阅管理</h1>
          <p className="text-muted-foreground">管理您的订阅计划和账单</p>
        </div>
      </div>

      {/* Current Plan */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Crown className="w-5 h-5" />
            当前计划
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-4 text-muted-foreground">加载中...</div>
          ) : (
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold">{currentPlan.name}</h3>
                <p className="text-muted-foreground">
                  ¥{currentPlan.price}/月
                  {subscription?.cancel_at_period_end && " (已取消续费)"}
                </p>
              </div>
              <div className="flex gap-2">
                {subscription?.plan !== "FREE" && (
                  <Button variant="outline" onClick={handleCancel}>
                    取消续费
                  </Button>
                )}
                <Button onClick={() => handleUpgrade("PRO")}>
                  <Zap className="w-4 h-4 mr-2" />
                  升级计划
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {plans.map(plan => (
          <Card
            key={plan.id}
            className={`relative ${subscription?.plan === plan.id ? "border-primary" : ""}`}
          >
            {subscription?.plan === plan.id && (
              <Badge className="absolute -top-2 right-4">当前</Badge>
            )}
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {plan.id === "ENTERPRISE" ? <Building className="w-5 h-5" /> : <CreditCard className="w-5 h-5" />}
                {plan.name}
              </CardTitle>
              <CardDescription>
                <span className="text-2xl font-bold text-foreground">¥{plan.price}</span>
                <span className="text-muted-foreground">/月</span>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {plan.features.map((f, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-primary" />
                  {f}
                </div>
              ))}
              {subscription?.plan !== plan.id && (
                <Button
                  className="w-full mt-4"
                  variant={plan.id === "PRO" ? "default" : "outline"}
                  onClick={() => handleUpgrade(plan.id)}
                >
                  {plan.price === 0 ? "降级" : "升级"}
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}