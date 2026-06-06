"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calendar, Clock, Trash2, Plus, Loader2 } from "lucide-react";
import { Loading } from "@/components/loading";

interface ScheduledItem {
  job_id: string;
  title: string;
  platform: string;
  scheduled_at: string;
  status: string;
  type?: string;
}

export function CalendarView() {
  const [items, setItems] = useState<ScheduledItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState(new Date());

  useEffect(() => {
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    try {
      // 模拟数据
      const mock: ScheduledItem[] = [
        { job_id: "1", title: "AI时代机会", platform: "抖音", scheduled_at: "2026-06-08T10:00:00", status: "scheduled" },
        { job_id: "2", title: "3个底层逻辑", platform: "小红书", scheduled_at: "2026-06-08T14:00:00", status: "scheduled" },
        { job_id: "3", title: "效率工具", platform: "B站", scheduled_at: "2026-06-09T09:00:00", status: "scheduled" },
        { job_id: "4", title: "自媒体真相", platform: "公众号", scheduled_at: "2026-06-10T20:00:00", status: "scheduled" },
        { job_id: "5", title: "AI工具推荐", platform: "抖音", scheduled_at: "2026-06-11T18:00:00", status: "scheduled" },
      ];
      setItems(mock);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const deleteItem = (jobId: string) => {
    setItems(items.filter((i) => i.job_id !== jobId));
  };

  if (loading) {
    return <Loading message="加载日历..." />;
  }

  // 按日期分组
  const grouped = items.reduce((acc, item) => {
    const date = new Date(item.scheduled_at).toLocaleDateString("zh-CN");
    if (!acc[date]) acc[date] = [];
    acc[date].push(item);
    return acc;
  }, {} as Record<string, ScheduledItem[]>);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Calendar className="h-7 w-7 text-orange-500" />
            内容日历
          </h1>
          <p className="text-muted-foreground">管理和调度内容发布时间</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          新建调度
        </Button>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-muted-foreground">本月已调度</div>
            <div className="text-2xl font-bold">{items.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-muted-foreground">待发布</div>
            <div className="text-2xl font-bold text-orange-500">
              {items.filter((i) => i.status === "scheduled").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-muted-foreground">已发布</div>
            <div className="text-2xl font-bold text-green-500">
              {items.filter((i) => i.status === "published").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-muted-foreground">活跃平台</div>
            <div className="text-2xl font-bold text-blue-500">
              {new Set(items.map((i) => i.platform)).size}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>近期调度</CardTitle>
          <CardDescription>所有待发布内容</CardDescription>
        </CardHeader>
        <CardContent>
          {Object.keys(grouped).length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">暂无调度任务</div>
          ) : (
            <div className="space-y-6">
              {Object.entries(grouped).map(([date, dayItems]) => (
                <div key={date}>
                  <div className="mb-2 flex items-center gap-2 text-sm font-medium text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    {date}
                  </div>
                  <div className="space-y-2">
                    {dayItems.map((item) => {
                      const time = new Date(item.scheduled_at).toLocaleTimeString("zh-CN", {
                        hour: "2-digit",
                        minute: "2-digit",
                      });
                      return (
                        <div
                          key={item.job_id}
                          className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent"
                        >
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-1 text-sm text-muted-foreground">
                              <Clock className="h-4 w-4" />
                              {time}
                            </div>
                            <div>
                              <div className="font-medium">{item.title}</div>
                              <div className="mt-1 flex items-center gap-2">
                                <Badge variant="outline">{item.platform}</Badge>
                                <Badge variant={item.status === "published" ? "default" : "secondary"}>
                                  {item.status === "published" ? "已发布" : "待发布"}
                                </Badge>
                              </div>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => deleteItem(item.job_id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
