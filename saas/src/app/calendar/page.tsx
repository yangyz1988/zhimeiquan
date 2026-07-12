"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Loading } from "@/components/loading";
import { toast } from "@/components/toaster";
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  Clock,
  Trash2,
  Plus,
  X,
  Filter,
  List,
  Grid3x3,
  CalendarDays,
  CheckCircle2,
  AlertCircle,
  Clock3,
  FileText,
  Smartphone,
  Monitor,
  ArrowUpDown,
  RotateCw,
  Loader2,
} from "lucide-react";

/* ============================================================
   Types
   ============================================================ */

interface CalendarItem {
  job_id: string;
  project_id?: string;
  platform: string;
  title: string;
  scheduled_at: string;
  status: "scheduled" | "published" | "failed" | "cancelled";
  content_type?: string;
}

interface CalendarData {
  items: CalendarItem[];
  total: number;
}

interface ScheduleForm {
  title: string;
  platform: string;
  scheduled_at: string;
  content_type: string;
}

type ViewMode = "calendar" | "list";
type FilterPlatform = string | "all";
type FilterStatus = string | "all";

/* ============================================================
   Constants
   ============================================================ */

const PLATFORMS = [
  "抖音", "小红书", "B站", "公众号", "快手",
  "微博", "知乎", "头条", "YouTube", "TikTok",
  "视频号", "百度热搜", "Instagram",
];

const CONTENT_TYPES = [
  "图文", "短视频", "中视频", "直播", "文章",
];

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  scheduled: { label: "待发布", color: "text-orange-400", bg: "bg-orange-500/15 border-orange-500/30" },
  published: { label: "已发布", color: "text-green-400", bg: "bg-green-500/15 border-green-500/30" },
  failed: { label: "失败", color: "text-red-400", bg: "bg-red-500/15 border-red-500/30" },
  cancelled: { label: "已取消", color: "text-gray-400", bg: "bg-gray-500/15 border-gray-500/30" },
};

const PLATFORM_COLORS: Record<string, string> = {
  "抖音": "#f97316", "小红书": "#ec4899", "B站": "#3b82f6",
  "公众号": "#22c55e", "快手": "#a855f7", "微博": "#f59e0b",
  "知乎": "#6366f1", "头条": "#dc2626", "YouTube": "#ef4444",
  "TikTok": "#06b6d4", "视频号": "#10b981", "百度热搜": "#f43f5e", "Instagram": "#e1306c",
};

const WEEK_DAYS = ["日", "一", "二", "三", "四", "五", "六"];

/* ============================================================
   Helpers
   ============================================================ */

function getMonthDays(year: number, month: number): (number | null)[] {
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const days: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) days.push(null);
  for (let i = 1; i <= daysInMonth; i++) days.push(i);
  while (days.length % 7 !== 0) days.push(null);
  return days;
}

function formatDate(year: number, month: number, day: number): string {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function formatTime(dateStr: string): string {
  const d = new Date(dateStr);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function formatDateTime(dateStr: string): string {
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function isToday(year: number, month: number, day: number): boolean {
  const now = new Date();
  return now.getFullYear() === year && now.getMonth() === month && now.getDate() === day;
}

function getWeekNumber(date: Date): number {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() + 3 - ((d.getDay() + 6) % 7));
  const week1 = new Date(d.getFullYear(), 0, 4);
  return 1 + Math.round(((d.getTime() - week1.getTime()) / 86400000 - 3 + ((week1.getDay() + 6) % 7)) / 7);
}

/* ============================================================
   Sub-components
   ============================================================ */

/** Platform badge with colour dot */
function PlatformBadge({ platform }: { platform: string }) {
  const color = PLATFORM_COLORS[platform] ?? "#8b5cf6";
  return (
    <span className="inline-flex items-center gap-1 text-xs font-medium" style={{ color }}>
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
      {platform}
    </span>
  );
}

/** Status badge */
function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, color: "text-gray-400", bg: "bg-gray-500/15 border-gray-500/30" };
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border ${cfg.bg} ${cfg.color}`}>
      {cfg.label}
    </span>
  );
}

/** Mini event card displayed in calendar day cells */
function MiniEventCard({ item, onDragStart }: { item: CalendarItem; onDragStart: (e: React.DragEvent, item: CalendarItem) => void }) {
  const color = PLATFORM_COLORS[item.platform] ?? "#8b5cf6";
  const time = formatTime(item.scheduled_at);
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, item)}
      className="group flex items-center gap-1 px-1.5 py-0.5 rounded cursor-grab active:cursor-grabbing
        hover:bg-white/10 transition-colors text-[11px] leading-tight"
      style={{ borderLeft: `2px solid ${color}` }}
    >
      <span className="text-white/40 font-mono text-[10px] shrink-0">{time}</span>
      <span className="text-white/80 truncate flex-1">{item.title}</span>
      <span className="text-white/30 opacity-0 group-hover:opacity-100 transition-opacity">&#x2630;</span>
    </div>
  );
}

/* ============================================================
   Main Calendar Page
   ============================================================ */

export default function CalendarPage() {
  const [items, setItems] = useState<CalendarItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<ViewMode>("calendar");
  const [filterPlatform, setFilterPlatform] = useState<FilterPlatform>("all");
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [draggedItem, setDraggedItem] = useState<CalendarItem | null>(null);
  const [dragOverDay, setDragOverDay] = useState<string | null>(null);
  const [listSortBy, setListSortBy] = useState<"date" | "platform" | "status">("date");
  const [listSortAsc, setListSortAsc] = useState(true);

  // Create form state
  const [formTitle, setFormTitle] = useState("");
  const [formPlatform, setFormPlatform] = useState("抖音");
  const [formTime, setFormTime] = useState("10:00");
  const [formContentType, setFormContentType] = useState("图文");
  const [formSaving, setFormSaving] = useState(false);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const days = useMemo(() => getMonthDays(year, month), [year, month]);

  /* ---- Data fetching ---- */
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);

  const fetchCalendar = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/calendar?year=${year}&month=${month + 1}`);
      if (res.ok) {
        const data: CalendarData = await res.json();
        setItems(data.items ?? []);
        setBackendConnected(true);
      } else {
        setItems([]);
        setBackendConnected(false);
        toast("获取日历数据失败", "error");
      }
    } catch {
      setItems([]);
      setBackendConnected(false);
      toast("网络错误，无法连接后端服务", "error");
    } finally {
      setLoading(false);
    }
  }, [year, month]);

  useEffect(() => {
    fetchCalendar();
  }, [fetchCalendar]);

  /* ---- Filtered items ---- */
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      if (filterPlatform !== "all" && item.platform !== filterPlatform) return false;
      if (filterStatus !== "all" && item.status !== filterStatus) return false;
      return true;
    });
  }, [items, filterPlatform, filterStatus]);

  /* ---- Items grouped by date ---- */
  const itemsByDate = useMemo(() => {
    const map = new Map<string, CalendarItem[]>();
    for (const item of filteredItems) {
      const dateKey = item.scheduled_at.slice(0, 10);
      if (!map.has(dateKey)) map.set(dateKey, []);
      map.get(dateKey)!.push(item);
    }
    return map;
  }, [filteredItems]);

  /* ---- Statistics ---- */
  const stats = useMemo(() => {
    const total = items.length;
    const published = items.filter((i) => i.status === "published").length;
    const scheduled = items.filter((i) => i.status === "scheduled").length;
    const failed = items.filter((i) => i.status === "failed").length;
    const cancelled = items.filter((i) => i.status === "cancelled").length;
    const platforms = new Set(items.map((i) => i.platform)).size;
    return { total, published, scheduled, failed, cancelled, platforms };
  }, [items]);

  /* ---- Navigation ---- */
  const goPrevMonth = () => setCurrentDate(new Date(year, month - 1, 1));
  const goNextMonth = () => setCurrentDate(new Date(year, month + 1, 1));
  const goToday = () => setCurrentDate(new Date());
  const monthLabel = `${year}年${month + 1}月`;

  /* ---- Create Schedule ---- */
  const openCreateModal = (day: number | null) => {
    if (day === null) return;
    setSelectedDate(formatDate(year, month, day));
    setFormTitle("");
    setFormPlatform("抖音");
    setFormTime("10:00");
    setFormContentType("图文");
    setShowCreateModal(true);
  };

  const handleCreateSchedule = async () => {
    if (!formTitle.trim()) {
      toast("请输入内容标题", "error");
      return;
    }
    setFormSaving(true);
    const scheduledAt = `${selectedDate}T${formTime}:00`;

    try {
      const res = await fetch("/api/calendar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: formTitle,
          platform: formPlatform,
          scheduled_at: scheduledAt,
          content_type: formContentType,
        }),
      });

      if (res.ok) {
        const newItem: CalendarItem = await res.json();
        setItems((prev) => [...prev, newItem]);
        toast("调度创建成功", "success");
        setShowCreateModal(false);
      } else {
        const errorData = await res.json().catch(() => ({}));
        toast(`创建失败: ${errorData.message || res.statusText}`, "error");
      }
    } catch {
      toast("网络错误，无法创建调度", "error");
    } finally {
      setFormSaving(false);
    }
  };

  /* ---- Delete Schedule ---- */
  const handleDelete = async (jobId: string) => {
    const prevItems = items;
    setItems((prev) => prev.filter((i) => i.job_id !== jobId));
    toast("调度已取消", "success");

    try {
      const res = await fetch(`/api/calendar/${jobId}`, { method: "DELETE" });
      if (!res.ok) {
        setItems(prevItems);
        const errorData = await res.json().catch(() => ({}));
        toast(`删除失败: ${errorData.message || res.statusText}`, "error");
      }
    } catch {
      setItems(prevItems);
      toast("网络错误，删除调度失败", "error");
    }
  };

  /* ---- Drag & Drop (native HTML5) ---- */
  const handleDragStart = (e: React.DragEvent, item: CalendarItem) => {
    setDraggedItem(item);
    e.dataTransfer.setData("text/plain", item.job_id);
    e.dataTransfer.effectAllowed = "move";
    if (e.currentTarget instanceof HTMLElement) {
      e.currentTarget.style.opacity = "0.5";
    }
  };

  const handleDragEnd = (e: React.DragEvent) => {
    if (e.currentTarget instanceof HTMLElement) {
      e.currentTarget.style.opacity = "1";
    }
    setDraggedItem(null);
    setDragOverDay(null);
  };

  const handleDragOver = (e: React.DragEvent, day: number | null) => {
    e.preventDefault();
    if (day === null) return;
    const dateKey = formatDate(year, month, day);
    setDragOverDay(dateKey);
  };

  const handleDragLeave = () => {
    setDragOverDay(null);
  };

  const handleDrop = async (e: React.DragEvent, day: number | null) => {
    e.preventDefault();
    if (day === null || !draggedItem) return;
    const newDate = formatDate(year, month, day);
    const oldTime = formatTime(draggedItem.scheduled_at);
    const newScheduledAt = `${newDate}T${oldTime}:00`;

    // Optimistic update
    const prevItems = items;
    setItems((prev) =>
      prev.map((item) =>
        item.job_id === draggedItem.job_id
          ? { ...item, scheduled_at: newScheduledAt }
          : item
      )
    );

    setDraggedItem(null);
    setDragOverDay(null);

    try {
      const res = await fetch(`/api/calendar/${draggedItem.job_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scheduled_at: newScheduledAt }),
      });
      if (res.ok) {
        toast("调度日期已更新", "success");
      } else {
        setItems(prevItems);
        const errorData = await res.json().catch(() => ({}));
        toast(`日期更新失败: ${errorData.message || res.statusText}`, "error");
      }
    } catch {
      setItems(prevItems);
      toast("网络错误，日期更新失败", "error");
    }
  };

  /* ---- Sorted list ---- */
  const sortedList = useMemo(() => {
    const arr = [...filteredItems];
    arr.sort((a, b) => {
      let cmp = 0;
      switch (listSortBy) {
        case "date":
          cmp = a.scheduled_at.localeCompare(b.scheduled_at);
          break;
        case "platform":
          cmp = a.platform.localeCompare(b.platform);
          break;
        case "status":
          cmp = a.status.localeCompare(b.status);
          break;
      }
      return listSortAsc ? cmp : -cmp;
    });
    return arr;
  }, [filteredItems, listSortBy, listSortAsc]);

  const toggleSort = (key: typeof listSortBy) => {
    if (listSortBy === key) {
      setListSortAsc((prev) => !prev);
    } else {
      setListSortBy(key);
      setListSortAsc(true);
    }
  };

  /* ---- Render ---- */
  if (loading) {
    return (
      <div className="relative min-h-screen">
        <div className="bg-grid pointer-events-none fixed inset-0 z-0" />
        <div className="relative z-10 max-w-7xl mx-auto px-4 py-6 sm:py-8 space-y-6">
          {/* Header skeleton */}
          <div className="flex items-center justify-between">
            <div>
              <div className="h-8 w-48 animate-pulse rounded bg-white/10" />
              <div className="mt-1 h-4 w-32 animate-pulse rounded bg-white/5" />
            </div>
            <div className="flex gap-2">
              <div className="h-8 w-20 animate-pulse rounded bg-white/10" />
              <div className="h-8 w-20 animate-pulse rounded bg-white/10" />
              <div className="h-8 w-24 animate-pulse rounded bg-orange-500/20" />
            </div>
          </div>
          {/* Stats skeleton */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="glass-card h-20 animate-pulse border-white/5" />
            ))}
          </div>
          {/* Calendar grid skeleton */}
          <div className="glass-card border-white/5 p-4 animate-pulse">
            <div className="grid grid-cols-7 gap-2">
              {Array.from({ length: 35 }).map((_, i) => (
                <div key={i} className="min-h-[100px] rounded bg-white/5" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen">
      {/* Background grid */}
      <div className="bg-grid pointer-events-none fixed inset-0 z-0" />

      {/* Glow effects */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full bg-orange-500/10 blur-[120px]" />
        <div className="absolute -top-20 -right-20 w-[400px] h-[400px] rounded-full bg-blue-500/10 blur-[120px]" />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full bg-purple-500/8 blur-[120px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 py-6 sm:py-8 space-y-6">
        {/* ---- Header ---- */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold flex items-center gap-2 text-white">
              <Calendar className="h-7 w-7 text-orange-400" />
              内容日历
            </h1>
            <p className="text-sm text-white/50 mt-1">管理和调度全平台内容发布时间</p>
          </div>
          <div className="flex items-center gap-2">
            {/* Connection status indicator */}
            {backendConnected === true && (
              <Badge variant="outline" className="border-green-500/30 bg-green-500/10 text-green-400 text-[10px]">
                <CheckCircle2 className="h-2.5 w-2.5 mr-1" />
                已连接后端
              </Badge>
            )}
            {backendConnected === false && (
              <Badge variant="outline" className="border-orange-500/30 bg-orange-500/10 text-orange-400 text-[10px]">
                <AlertCircle className="h-2.5 w-2.5 mr-1" />
                本地模式
              </Badge>
            )}
            {backendConnected === null && (
              <Badge variant="outline" className="border-white/10 text-white/30 text-[10px] animate-pulse">
                <Loader2 className="h-2.5 w-2.5 mr-1 animate-spin" />
                连接中...
              </Badge>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchCalendar()}
              disabled={loading}
              className="border-white/10 text-white/70 hover:bg-white/10 hover:text-white text-xs"
            >
              <RotateCw className={`h-3.5 w-3.5 mr-1 ${loading ? "animate-spin" : ""}`} />
              同步后端
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setViewMode(viewMode === "calendar" ? "list" : "calendar")}
              className="border-white/10 text-white/70 hover:bg-white/10 hover:text-white"
            >
              {viewMode === "calendar" ? (
                <><List className="h-4 w-4 mr-1" />列表视图</>
              ) : (
                <><Grid3x3 className="h-4 w-4 mr-1" />日历视图</>
              )}
            </Button>
            <Button
              size="sm"
              onClick={() => openCreateModal(new Date().getDate())}
              className="bg-orange-500/80 hover:bg-orange-500 text-white"
            >
              <Plus className="h-4 w-4 mr-1" />新建调度
            </Button>
          </div>
        </div>

        {/* ---- Statistics Bar ---- */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { label: "本月总计", value: stats.total, icon: CalendarDays, color: "text-white" },
            { label: "待发布", value: stats.scheduled, icon: Clock3, color: "text-orange-400" },
            { label: "已发布", value: stats.published, icon: CheckCircle2, color: "text-green-400" },
            { label: "失败", value: stats.failed, icon: AlertCircle, color: "text-red-400" },
            { label: "已取消", value: stats.cancelled, icon: X, color: "text-gray-400" },
            { label: "活跃平台", value: stats.platforms, icon: Monitor, color: "text-blue-400" },
          ].map((stat) => {
            const Icon = stat.icon;
            return (
              <Card key={stat.label} className="glass-card border-white/5">
                <CardContent className="p-3 sm:p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-[11px] text-white/40">{stat.label}</div>
                      <div className={`text-xl sm:text-2xl font-bold mt-0.5 ${stat.color}`}>{stat.value}</div>
                    </div>
                    <Icon className={`h-5 w-5 ${stat.color} opacity-40`} />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* ---- Filters ---- */}
        <Card className="glass-card border-white/5">
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center gap-2 sm:gap-4 flex-wrap">
              <Filter className="h-4 w-4 text-white/40" />
              <span className="text-xs text-white/50">筛选:</span>

              <select
                value={filterPlatform}
                onChange={(e) => setFilterPlatform(e.target.value)}
                className="bg-white/5 border border-white/10 rounded-md px-2.5 py-1.5 text-xs text-white/70
                  focus:outline-none focus:border-orange-400/50 appearance-none cursor-pointer hover:bg-white/10"
              >
                <option value="all">全部平台</option>
                {PLATFORMS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>

              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="bg-white/5 border border-white/10 rounded-md px-2.5 py-1.5 text-xs text-white/70
                  focus:outline-none focus:border-orange-400/50 appearance-none cursor-pointer hover:bg-white/10"
              >
                <option value="all">全部状态</option>
                <option value="scheduled">待发布</option>
                <option value="published">已发布</option>
                <option value="failed">失败</option>
                <option value="cancelled">已取消</option>
              </select>

              {items.length !== filteredItems.length && (
                <button
                  onClick={() => { setFilterPlatform("all"); setFilterStatus("all"); }}
                  className="text-xs text-orange-400 hover:text-orange-300 underline"
                >
                  清除筛选 ({filteredItems.length}/{items.length})
                </button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* ---- Main content: Calendar / List ---- */}
        {filteredItems.length === 0 && items.length === 0 ? (
          <Card className="glass-card border-white/5">
            <CardContent className="flex flex-col items-center justify-center py-16 gap-4">
              <CalendarDays className="h-16 w-16 text-white/15" />
              <div className="text-center">
                <p className="text-lg font-medium text-white/50">本月暂无调度</p>
                <p className="text-sm text-white/30 mt-1">点击下方"新建调度"按钮添加首个任务</p>
              </div>
              <Button
                size="sm"
                onClick={() => openCreateModal(new Date().getDate())}
                className="bg-orange-500/80 hover:bg-orange-500 text-white"
              >
                <Plus className="h-4 w-4 mr-1" />新建调度
              </Button>
            </CardContent>
          </Card>
        ) : viewMode === "calendar" ? (
          /* ========== CALENDAR GRID ========== */
          <Card className="glass-card border-white/5 overflow-hidden">
            {/* Month navigation */}
            <div className="flex items-center justify-between p-4 border-b border-white/5">
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={goPrevMonth}
                  className="h-8 w-8 text-white/50 hover:text-white hover:bg-white/10"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <h2 className="text-lg font-semibold text-white min-w-[140px] text-center">{monthLabel}</h2>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={goNextMonth}
                  className="h-8 w-8 text-white/50 hover:text-white hover:bg-white/10"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={goToday}
                className="border-white/10 text-white/60 hover:text-white hover:bg-white/10 text-xs"
              >
                今天
              </Button>
            </div>

            {/* Weekday headers */}
            <div className="grid grid-cols-7 border-b border-white/5">
              {WEEK_DAYS.map((d) => (
                <div
                  key={d}
                  className="p-2 text-center text-xs font-medium text-white/40 border-r border-white/5 last:border-r-0"
                >
                  {d}
                </div>
              ))}
            </div>

            {/* Day cells */}
            <div className="grid grid-cols-7">
              {days.map((day, idx) => {
                if (day === null) {
                  return <div key={`empty-${idx}`} className="min-h-[100px] sm:min-h-[120px] border-r border-b border-white/5 bg-white/[0.01]" />;
                }
                const dateKey = formatDate(year, month, day);
                const dayItems = itemsByDate.get(dateKey) ?? [];
                const today = isToday(year, month, day);
                const isOver = dragOverDay === dateKey;

                return (
                  <div
                    key={dateKey}
                    onClick={() => openCreateModal(day)}
                    onDragOver={(e) => handleDragOver(e, day)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, day)}
                    className={`
                      min-h-[100px] sm:min-h-[120px] p-1.5 sm:p-2
                      border-r border-b border-white/5 last:border-r-0
                      cursor-pointer transition-all duration-200
                      ${today ? "bg-orange-500/5" : "hover:bg-white/[0.03]"}
                      ${isOver ? "bg-orange-500/10 ring-1 ring-orange-400/30" : ""}
                      relative
                    `}
                  >
                    {/* Day number */}
                    <div className={`
                      inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium mb-1
                      ${today ? "bg-orange-500 text-white" : "text-white/60"}
                    `}>
                      {day}
                    </div>

                    {/* Events */}
                    <div className="space-y-0.5">
                      {dayItems.slice(0, 3).map((item) => (
                        <MiniEventCard key={item.job_id} item={item} onDragStart={handleDragStart} />
                      ))}
                      {dayItems.length > 3 && (
                        <div className="text-[10px] text-white/30 pl-1">
                          +{dayItems.length - 3} 更多
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        ) : (
          /* ========== LIST VIEW ========== */
          <Card className="glass-card border-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="text-white/80 text-base flex items-center gap-2">
                <List className="h-4 w-4 text-orange-400" />
                调度列表
                <span className="text-xs font-normal text-white/30 ml-1">({filteredItems.length} 项)</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {sortedList.length === 0 && filteredItems.length > 0 ? (
                <div className="py-12 text-center">
                  <Filter className="h-8 w-8 text-white/20 mx-auto mb-2" />
                  <p className="text-sm text-white/40">筛选条件下没有匹配项</p>
                  <button
                    onClick={() => { setFilterPlatform("all"); setFilterStatus("all"); }}
                    className="mt-2 text-xs text-orange-400 hover:text-orange-300 underline"
                  >
                    清除筛选条件
                  </button>
                </div>
              ) : sortedList.length === 0 ? (
                <div className="py-12 text-center text-white/30 text-sm">暂无调度任务</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/5">
                        <th
                          className="text-left p-3 text-white/40 font-medium text-xs cursor-pointer hover:text-white/60"
                          onClick={() => toggleSort("date")}
                        >
                          <span className="inline-flex items-center gap-1">
                            时间
                            {listSortBy === "date" && <ArrowUpDown className={`h-3 w-3 ${listSortAsc ? "" : "rotate-180"}`} />}
                          </span>
                        </th>
                        <th className="text-left p-3 text-white/40 font-medium text-xs">标题</th>
                        <th
                          className="text-left p-3 text-white/40 font-medium text-xs cursor-pointer hover:text-white/60"
                          onClick={() => toggleSort("platform")}
                        >
                          <span className="inline-flex items-center gap-1">
                            平台
                            {listSortBy === "platform" && <ArrowUpDown className={`h-3 w-3 ${listSortAsc ? "" : "rotate-180"}`} />}
                          </span>
                        </th>
                        <th className="text-left p-3 text-white/40 font-medium text-xs">类型</th>
                        <th
                          className="text-left p-3 text-white/40 font-medium text-xs cursor-pointer hover:text-white/60"
                          onClick={() => toggleSort("status")}
                        >
                          <span className="inline-flex items-center gap-1">
                            状态
                            {listSortBy === "status" && <ArrowUpDown className={`h-3 w-3 ${listSortAsc ? "" : "rotate-180"}`} />}
                          </span>
                        </th>
                        <th className="text-right p-3 text-white/40 font-medium text-xs">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedList.map((item) => (
                        <tr key={item.job_id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                          <td className="p-3 text-white/60 text-xs whitespace-nowrap">
                            <span className="inline-flex items-center gap-1">
                              <Clock className="h-3.5 w-3.5 text-white/30" />
                              {formatDateTime(item.scheduled_at)}
                            </span>
                          </td>
                          <td className="p-3 text-white/80 font-medium">{item.title}</td>
                          <td className="p-3"><PlatformBadge platform={item.platform} /></td>
                          <td className="p-3 text-white/50 text-xs">{item.content_type ?? "-"}</td>
                          <td className="p-3"><StatusBadge status={item.status} /></td>
                          <td className="p-3 text-right">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={(e) => { e.stopPropagation(); handleDelete(item.job_id); }}
                              className="h-7 w-7 text-white/30 hover:text-red-400 hover:bg-red-500/10"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* ---- Dragging indicator ---- */}
        {draggedItem && (
          <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
            <div className="glass-card px-4 py-2 rounded-lg border-orange-400/30 bg-orange-500/10 shadow-lg">
              <div className="flex items-center gap-2 text-sm text-white/80">
                <span className="text-white/50">正在移动:</span>
                <span className="font-medium">{draggedItem.title}</span>
                <span className="text-white/30">|</span>
                <PlatformBadge platform={draggedItem.platform} />
              </div>
            </div>
          </div>
        )}

        {/* ========== CREATE SCHEDULE MODAL ========== */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div
              className="glass-card w-full max-w-md mx-4 border-white/10 rounded-xl overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal header */}
              <div className="flex items-center justify-between p-5 border-b border-white/5">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Plus className="h-5 w-5 text-orange-400" />
                  新建调度
                </h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-white/30 hover:text-white/70 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Modal body */}
              <div className="p-5 space-y-4">
                <div>
                  <label className="block text-xs font-medium text-white/50 mb-1.5">内容标题</label>
                  <Input
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                    placeholder="输入发布内容标题"
                    className="border-white/10 bg-white/[0.03] text-white placeholder:text-white/20 focus:border-orange-400/50"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-white/50 mb-1.5">平台</label>
                    <select
                      value={formPlatform}
                      onChange={(e) => setFormPlatform(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-2 text-sm text-white/70
                        focus:outline-none focus:border-orange-400/50 appearance-none cursor-pointer hover:bg-white/10"
                    >
                      {PLATFORMS.map((p) => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-white/50 mb-1.5">内容类型</label>
                    <select
                      value={formContentType}
                      onChange={(e) => setFormContentType(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-2 text-sm text-white/70
                        focus:outline-none focus:border-orange-400/50 appearance-none cursor-pointer hover:bg-white/10"
                    >
                      {CONTENT_TYPES.map((t) => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-white/50 mb-1.5">发布日期</label>
                    <Input
                      type="date"
                      value={selectedDate}
                      onChange={(e) => setSelectedDate(e.target.value)}
                      className="border-white/10 bg-white/[0.03] text-white focus:border-orange-400/50 [color-scheme:dark]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-white/50 mb-1.5">时间</label>
                    <Input
                      type="time"
                      value={formTime}
                      onChange={(e) => setFormTime(e.target.value)}
                      className="border-white/10 bg-white/[0.03] text-white focus:border-orange-400/50 [color-scheme:dark]"
                    />
                  </div>
                </div>
              </div>

              {/* Modal footer */}
              <div className="flex justify-end gap-3 p-5 border-t border-white/5">
                <Button
                  variant="outline"
                  onClick={() => setShowCreateModal(false)}
                  className="border-white/10 text-white/60 hover:bg-white/10 hover:text-white"
                >
                  取消
                </Button>
                <Button
                  onClick={handleCreateSchedule}
                  disabled={formSaving}
                  className="bg-orange-500/80 hover:bg-orange-500 text-white"
                >
                  {formSaving ? "创建中..." : "创建调度"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
