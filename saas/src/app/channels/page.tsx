"use client";

import { useState, useEffect } from "react";
import { Radio, Plus, Settings, TrendingUp, Trash2, RefreshCw } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/components/toaster";
import { apiFetch } from "@/lib/api";

interface Channel {
  id: string;
  name: string;
  platform: string;
  channel_type: string;
  account_name?: string;
  is_active: boolean;
  health_status: string;
  followers?: number;
  engagement?: number;
  created_at: string;
}

const platforms = ["抖音", "小红书", "B站", "快手", "微博", "知乎", "头条", "公众号", "视频号", "YouTube", "TikTok", "Instagram"];

export default function ChannelsPage() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newChannel, setNewChannel] = useState({ name: "", platform: "抖音", account_name: "" });

  useEffect(() => {
    loadChannels();
  }, []);

  const loadChannels = async () => {
    setLoading(true);
    try {
      const result = await apiFetch<{ channels: Channel[] }>("/api/channels");
      if (result.ok && result.data) setChannels(result.data.channels);
    } catch {
      setChannels([
        { id: "1", name: "主账号", platform: "抖音", channel_type: "SOCIAL", account_name: "@demo", is_active: true, health_status: "HEALTHY", followers: 10000, engagement: 0.05, created_at: new Date().toISOString() },
        { id: "2", name: "矩阵号", platform: "小红书", channel_type: "SOCIAL", account_name: "@demo2", is_active: true, health_status: "WARNING", followers: 5000, engagement: 0.03, created_at: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!newChannel.name.trim()) {
      toast("请输入渠道名称", "error");
      return;
    }

    try {
      const result = await apiFetch("/api/channels", {
        method: "POST",
        body: newChannel,
      });
      if (result.ok) {
        toast("渠道添加成功", "success");
        setShowAdd(false);
        setNewChannel({ name: "", platform: "抖音", account_name: "" });
        loadChannels();
      }
    } catch {
      toast("添加失败", "error");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const result = await apiFetch(`/api/channels?id=${id}`, { method: "DELETE" });
      if (result.ok) {
        setChannels(channels.filter(c => c.id !== id));
        toast("删除成功", "success");
      }
    } catch {
      toast("删除失败", "error");
    }
  };

  const handleToggle = async (id: string, active: boolean) => {
    try {
      const result = await apiFetch(`/api/channels?id=${id}`, {
        method: "PATCH",
        body: { is_active: !active },
      });
      if (result.ok) {
        setChannels(channels.map(c =>
          c.id === id ? { ...c, is_active: !active } : c
        ));
      }
    } catch {
      toast("操作失败", "error");
    }
  };

  const getHealthBadge = (status: string) => {
    const map: Record<string, "default" | "secondary" | "destructive"> = {
      HEALTHY: "default",
      WARNING: "secondary",
      CRITICAL: "destructive",
      UNKNOWN: "secondary",
    };
    const labels: Record<string, string> = {
      HEALTHY: "健康",
      WARNING: "警告",
      CRITICAL: "异常",
      UNKNOWN: "未知",
    };
    return <Badge variant={map[status] || "secondary"}>{labels[status] || status}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">分发渠道</h1>
          <p className="text-muted-foreground">管理内容分发渠道和账号</p>
        </div>
        <Button onClick={() => setShowAdd(!showAdd)}>
          <Plus className="w-4 h-4 mr-2" />
          添加渠道
        </Button>
      </div>

      {showAdd && (
        <Card>
          <CardHeader>
            <CardTitle>添加新渠道</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <input
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="渠道名称"
                value={newChannel.name}
                onChange={e => setNewChannel({ ...newChannel, name: e.target.value })}
              />
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={newChannel.platform}
                onChange={e => setNewChannel({ ...newChannel, platform: e.target.value })}
              >
                {platforms.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
              <input
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="账号名称"
                value={newChannel.account_name}
                onChange={e => setNewChannel({ ...newChannel, account_name: e.target.value })}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleAdd}>确认添加</Button>
              <Button variant="outline" onClick={() => setShowAdd(false)}>取消</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full text-center py-12 text-muted-foreground">加载中...</div>
        ) : channels.length === 0 ? (
          <div className="col-span-full text-center py-12 text-muted-foreground">
            <Radio className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>暂无渠道</p>
            <p className="text-sm">点击上方按钮添加</p>
          </div>
        ) : (
          channels.map(channel => (
            <Card key={channel.id}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{channel.name}</CardTitle>
                  {getHealthBadge(channel.health_status)}
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Badge variant="outline">{channel.platform}</Badge>
                  {channel.account_name && <span>{channel.account_name}</span>}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-muted-foreground">粉丝数</p>
                    <p className="text-lg font-bold">{channel.followers?.toLocaleString() || "-"}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">互动率</p>
                    <p className="text-lg font-bold">{channel.engagement ? `${(channel.engagement * 100).toFixed(1)}%` : "-"}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => handleToggle(channel.id, channel.is_active)}
                  >
                    {channel.is_active ? "停用" : "启用"}
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => handleDelete(channel.id)}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}