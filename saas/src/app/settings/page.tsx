"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageBackground } from "@/components/ui/page-layout";
import { toast } from "@/components/toaster";
import {
  User, Bell, Users, Save, Mail, Shield, Globe, Smartphone,
  Eye, EyeOff, Trash2, UserPlus, Crown,
} from "lucide-react";

/* -------------------------------------------------------- */
/*  自定义 Toggle 开关                                        */
/* -------------------------------------------------------- */

function Toggle({ checked, onChange, disabled = false }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 ${
        checked ? "bg-orange-500" : "bg-white/10"
      } ${disabled ? "opacity-40 cursor-not-allowed" : ""}`}
    >
      <span
        className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow-lg transform ring-0 transition duration-200 ease-in-out ${
          checked ? "translate-x-5" : "translate-x-0.5"
        }`}
      />
    </button>
  );
}

/* -------------------------------------------------------- */
/*  团队角色 Badge 映射                                       */
/* -------------------------------------------------------- */

function RoleBadge({ role }: { role: string }) {
  const map: Record<string, { label: string; className: string }> = {
    admin: { label: "管理员", className: "bg-orange-500/15 text-orange-400 border-orange-500/30" },
    editor: { label: "编辑", className: "bg-blue-500/15 text-blue-400 border-blue-500/30" },
    viewer: { label: "只读", className: "bg-white/5 text-white/50 border-white/10" },
  };
  const config = map[role] ?? map.viewer;
  return (
    <Badge className={`border ${config.className}`}>
      {config.label}
    </Badge>
  );
}

/* -------------------------------------------------------- */
/*  Section: 个人信息                                         */
/* -------------------------------------------------------- */

function ProfileSection() {
  const [name, setName] = useState("张三");
  const [email] = useState("zhangsan@example.com");
  const [showEmail, setShowEmail] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleSave = () => {
    setSaving(true);
    setTimeout(() => {
      toast("个人信息已保存", "success");
      setSaving(false);
    }, 800);
  };

  return (
    <Card className="glass-card glow-orange">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-500/10">
            <User className="h-5 w-5 text-orange-400" />
          </div>
          <div>
            <CardTitle className="text-white text-lg">个人信息</CardTitle>
            <CardDescription className="text-white/50">管理你的个人资料和账户信息</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* 头像区域 */}
        <div className="flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-orange-500 to-pink-500 text-white text-xl font-bold shrink-0">
            {name.charAt(0)}
          </div>
          <div>
            <p className="text-sm text-white/70 font-medium">{name}</p>
            <p className="text-xs text-white/40">点击头像可更换</p>
          </div>
        </div>

        {/* 姓名 */}
        <div className="space-y-1.5">
          <label className="text-xs text-white/40 uppercase tracking-wider">姓名</label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="bg-white/5 border-white/10 text-white placeholder:text-white/20 focus-visible:ring-orange-400"
            placeholder="输入你的姓名"
          />
        </div>

        {/* 邮箱 */}
        <div className="space-y-1.5">
          <label className="text-xs text-white/40 uppercase tracking-wider">邮箱</label>
          <div className="flex items-center gap-2">
            <div className="flex-1 flex items-center gap-2 rounded-md border border-white/10 bg-white/5 px-3 py-2">
              <Mail className="h-4 w-4 text-white/30 shrink-0" />
              <span className="text-sm text-white/60 font-mono">
                {showEmail ? email : email.replace(/(.{2}).*(@.*)/, "$1***$2")}
              </span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowEmail(!showEmail)}
              className="text-white/40 hover:text-white hover:bg-white/10 shrink-0"
            >
              {showEmail ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        {/* 保存按钮 */}
        <div className="flex justify-end pt-2">
          <Button
            onClick={handleSave}
            disabled={saving}
            className="bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600"
          >
            <Save className="mr-2 h-4 w-4" />
            {saving ? "保存中..." : "保存修改"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/* -------------------------------------------------------- */
/*  Section: 通知设置                                         */
/* -------------------------------------------------------- */

function NotificationSection() {
  const [notifications, setNotifications] = useState({
    emailWeekly: true,
    emailProduct: false,
    pushHotspot: true,
    pushSystem: true,
    pushMarketing: false,
  });

  const toggle = (key: keyof typeof notifications) => {
    setNotifications((prev) => ({ ...prev, [key]: !prev[key] }));
    const labels: Record<keyof typeof notifications, string> = {
      emailWeekly: "周报邮件",
      emailProduct: "产品更新",
      pushHotspot: "热点提醒",
      pushSystem: "系统通知",
      pushMarketing: "营销活动",
    };
    toast(`「${labels[key]}」已${notifications[key] ? "关闭" : "开启"}`, "success");
  };

  const items: { key: keyof typeof notifications; icon: React.ElementType; label: string; desc: string; color: string }[] = [
    { key: "emailWeekly", icon: Mail, label: "周报邮件", desc: "每周一收到爆款规则周报", color: "text-blue-400" },
    { key: "emailProduct", icon: Mail, label: "产品更新", desc: "新功能上线和版本更新通知", color: "text-purple-400" },
    { key: "pushHotspot", icon: Globe, label: "热点提醒", desc: "平台热点实时推送提醒", color: "text-orange-400" },
    { key: "pushSystem", icon: Shield, label: "系统通知", desc: "账户安全和服务状态通知", color: "text-green-400" },
    { key: "pushMarketing", icon: Smartphone, label: "营销活动", desc: "优惠活动和限时促销信息", color: "text-pink-400" },
  ];

  return (
    <Card className="glass-card glow-blue">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
            <Bell className="h-5 w-5 text-blue-400" />
          </div>
          <div>
            <CardTitle className="text-white text-lg">通知设置</CardTitle>
            <CardDescription className="text-white/50">管理你的通知偏好</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="divide-y divide-white/5">
          {items.map(({ key, icon: Icon, label, desc, color }) => (
            <div key={key} className="flex items-center justify-between py-4 first:pt-0 last:pb-0">
              <div className="flex items-center gap-3 min-w-0">
                <Icon className={`h-4 w-4 ${color} shrink-0`} />
                <div className="min-w-0">
                  <p className="text-sm text-white/80 font-medium truncate">{label}</p>
                  <p className="text-xs text-white/40 truncate">{desc}</p>
                </div>
              </div>
              <Toggle
                checked={notifications[key]}
                onChange={() => toggle(key)}
              />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/* -------------------------------------------------------- */
/*  Section: 团队管理                                         */
/* -------------------------------------------------------- */

function TeamSection() {
  const [members] = useState([
    { id: 1, name: "张三", email: "zhangsan@example.com", role: "admin", avatar: "张" },
    { id: 2, name: "李四", email: "lisi@example.com", role: "editor", avatar: "李" },
    { id: 3, name: "王五", email: "wangwu@example.com", role: "viewer", avatar: "王" },
  ]);

  const handleInvite = () => {
    toast("邀请功能即将上线，敬请期待", "success");
  };

  const handleRemove = (name: string) => {
    toast(`成员「${name}」移除功能即将上线`, "success");
  };

  return (
    <Card className="glass-card glow-purple">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10">
              <Users className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <CardTitle className="text-white text-lg">团队管理</CardTitle>
              <CardDescription className="text-white/50">{members.length} 位团队成员</CardDescription>
            </div>
          </div>
          <Button
            size="sm"
            onClick={handleInvite}
            className="bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600"
          >
            <UserPlus className="mr-1.5 h-3.5 w-3.5" />
            邀请成员
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="divide-y divide-white/5">
          {members.map((member) => (
            <div
              key={member.id}
              className="flex items-center gap-3 py-3 first:pt-0 last:pb-0"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-white/70 text-sm font-medium shrink-0">
                {member.avatar}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm text-white/80 font-medium truncate">
                    {member.name}
                  </p>
                  {member.role === "admin" && (
                    <Crown className="h-3.5 w-3.5 text-orange-400 shrink-0" />
                  )}
                </div>
                <p className="text-xs text-white/40 truncate">{member.email}</p>
              </div>
              <RoleBadge role={member.role} />
              {member.role !== "admin" && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleRemove(member.name)}
                  className="text-white/20 hover:text-red-400 hover:bg-red-500/10 shrink-0"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/* -------------------------------------------------------- */
/*  Settings Page                                            */
/* -------------------------------------------------------- */

export default function SettingsPage() {
  return (
    <div className="relative">
      <PageBackground
        color1="bg-orange-500/[0.05]"
        color2="bg-purple-500/[0.05]"
      />

      <div className="relative z-10 container space-y-10 py-8 sm:py-12">
        {/* 页面标题 */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-white sm:text-4xl">
            账户<span className="text-gradient">设置</span>
          </h1>
          <p className="text-sm sm:text-base text-white/50 max-w-lg mx-auto">
            管理你的个人资料、通知偏好和团队协作
          </p>
        </div>

        {/* 内容区域 */}
        <div className="mx-auto max-w-2xl space-y-6">
          <ProfileSection />
          <NotificationSection />
          <TeamSection />
        </div>
      </div>
    </div>
  );
}
