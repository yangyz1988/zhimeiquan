"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import {
  Crown, Eye, MessageSquare, Shield, Type, Cpu, BookOpen, PenTool, Target,
  ArrowRight, FolderOpen, FileText, Search, ChevronDown, ChevronRight,
  CalendarDays, RefreshCw, Clock, Tag, Save, X, Menu, BookMarked,
  FileEdit, EyeIcon, ListTree, Layers, Loader2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/toaster";

/* ============================================================
   Types
   ============================================================ */

interface TreeNode {
  id: string;
  name: string;
  path: string;
  type: "folder" | "file";
  children?: TreeNode[];
  size?: number;
  modified?: string;
}

interface FileContent {
  path: string;
  content: string;
  meta: {
    size: number;
    modified: string;
    wordCount: number;
    tags: string[];
    fileName: string;
  };
}

/* ============================================================
   Constants — 9-layer timeline data (kept from original)
   ============================================================ */

const layers = [
  {
    level: "L9", title: "专家智能体", desc: "50+专家 4层级协作",
    color: "purple", glowClass: "glow-purple", icon: Crown,
    badgeBg: "dark:bg-purple-950/60 dark:text-purple-300 bg-purple-100 text-purple-700",
  },
  {
    level: "L8", title: "视觉音频优化", desc: "封面+配图+口播节奏",
    color: "purple-600", glowClass: "glow-purple", icon: Eye,
    badgeBg: "dark:bg-purple-950/60 dark:text-purple-300 bg-purple-100 text-purple-700",
  },
  {
    level: "L7", title: "运营SOP体系", desc: "评论区+冷启动+数据回流",
    color: "indigo-500", glowClass: "glow-blue", icon: MessageSquare,
    badgeBg: "dark:bg-indigo-950/60 dark:text-indigo-300 bg-indigo-100 text-indigo-700",
  },
  {
    level: "L6", title: "爆款概率保障", desc: "概率提升至95%+",
    color: "blue", glowClass: "glow-blue", icon: Shield,
    badgeBg: "dark:bg-blue-950/60 dark:text-blue-300 bg-blue-100 text-blue-700",
  },
  {
    level: "L5", title: "标题类型库", desc: "13种爆款标题类型",
    color: "sky-500", glowClass: "", icon: Type,
    badgeBg: "dark:bg-sky-950/60 dark:text-sky-300 bg-sky-100 text-sky-700",
  },
  {
    level: "L4", title: "平台算法适配", desc: "13个平台核心指标",
    color: "teal-500", glowClass: "", icon: Cpu,
    badgeBg: "dark:bg-teal-950/60 dark:text-teal-300 bg-teal-100 text-teal-700",
  },
  {
    level: "L3", title: "六大方法论", desc: "反常识+人性+数字...",
    color: "green", glowClass: "", icon: BookOpen,
    badgeBg: "dark:bg-green-950/60 dark:text-green-300 bg-green-100 text-green-700",
  },
  {
    level: "L2", title: "四步创作法", desc: "选题→开头→正文→结尾",
    color: "lime-500", glowClass: "", icon: PenTool,
    badgeBg: "dark:bg-lime-950/60 dark:text-lime-300 bg-lime-100 text-lime-700",
  },
  {
    level: "L1", title: "爆款底层逻辑", desc: "CTR核心公式",
    color: "amber", glowClass: "", icon: Target,
    badgeBg: "dark:bg-amber-950/60 dark:text-amber-300 bg-amber-100 text-amber-700",
  },
];

const quickLinks = [
  {
    title: "内容生成", desc: "开始创作爆款内容", href: "/generate",
    glowClass: "glow-orange", icon: PenTool, iconColor: "text-orange-400",
  },
  {
    title: "专家引擎", desc: "获取专家定制方案", href: "/experts",
    glowClass: "glow-purple", icon: Cpu, iconColor: "text-purple-400",
  },
  {
    title: "运营中心", desc: "冷启动+运营SOP", href: "/operations",
    glowClass: "glow-green", icon: MessageSquare, iconColor: "text-green-400",
  },
];

const CATEGORY_ICONS: Record<string, typeof FolderOpen> = {
  methodology: BookOpen, templates: FileText, experts: Crown, prompts: PenTool,
};

const CATEGORY_LABELS: Record<string, string> = {
  methodology: "方法论", templates: "模板库", experts: "专家库", prompts: "提示词",
};

const CATEGORY_COLORS: Record<string, string> = {
  methodology: "text-green-400", templates: "text-blue-400",
  experts: "text-purple-400", prompts: "text-orange-400",
};

const CATEGORY_GLOWS: Record<string, string> = {
  methodology: "glow-green", templates: "glow-blue",
  experts: "glow-purple", prompts: "glow-orange",
};

const CATEGORY_BADGE_COLORS: Record<string, string> = {
  methodology: "bg-green-500/15 text-green-300 border-green-500/30",
  templates: "bg-blue-500/15 text-blue-300 border-blue-500/30",
  experts: "bg-purple-500/15 text-purple-300 border-purple-500/30",
  prompts: "bg-orange-500/15 text-orange-300 border-orange-500/30",
};

/* ============================================================
   Sub-components
   ============================================================ */

/** Tree node with expand/collapse */
function TreeItem({
  node,
  selectedPath,
  depth,
  onSelect,
}: {
  node: TreeNode;
  selectedPath: string;
  depth: number;
  onSelect: (path: string) => void;
}) {
  const [expanded, setExpanded] = useState(depth < 1);

  if (node.type === "folder") {
    const isRootCategory = depth === 0;
    const catKey = node.id;
    const Icon = CATEGORY_ICONS[catKey] ?? FolderOpen;
    const label = CATEGORY_LABELS[catKey] ?? node.name;
    const catColor = CATEGORY_COLORS[catKey] ?? "text-white/60";

    return (
      <div>
        <button
          onClick={() => setExpanded(!expanded)}
          className={`
            w-full flex items-center gap-2 px-3 py-2 text-left rounded-lg
            transition-all duration-200 group
            ${isRootCategory
              ? "text-white/80 font-medium"
              : "text-white/60 text-sm"
            }
            hover:bg-white/5 hover:text-white
          `}
        >
          <span className="shrink-0">
            {expanded ? <ChevronDown className="h-3.5 w-3.5 text-white/30" /> : <ChevronRight className="h-3.5 w-3.5 text-white/30" />}
          </span>
          <Icon className={`h-4 w-4 shrink-0 ${isRootCategory ? catColor : "text-white/40"}`} />
          <span className="truncate flex-1">{label}</span>
          {node.children && (
            <span className="text-[10px] text-white/30 shrink-0">{node.children.length}</span>
          )}
        </button>
        {expanded && node.children && (
          <div className="ml-2 pl-2 border-l border-white/5">
            {node.children.map((child) => (
              <TreeItem
                key={child.id}
                node={child}
                selectedPath={selectedPath}
                depth={depth + 1}
                onSelect={onSelect}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  // File node
  const displayName = node.name.replace(/\.md$/, "").replace(/^[\d]+-/, "");
  const catPrefix = node.path.split("/")[0];
  const isSelected = selectedPath === node.path;

  return (
    <button
      onClick={() => onSelect(node.path)}
      className={`
        w-full flex items-center gap-2 px-3 py-1.5 text-left rounded-lg
        transition-all duration-200 text-sm group
        ${isSelected
          ? "bg-orange-500/10 text-orange-300 border border-orange-500/20"
          : "text-white/50 hover:text-white/80 hover:bg-white/5"
        }
      `}
    >
      <FileText className="h-3.5 w-3.5 shrink-0 text-white/30" />
      <span className="truncate flex-1 text-xs">{displayName}</span>
      {node.modified && (
        <span className="text-[9px] text-white/20 shrink-0 hidden sm:inline">
          {new Date(node.modified).toLocaleDateString("zh-CN")}
        </span>
      )}
    </button>
  );
}

/** Simple Markdown preview */
function MarkdownPreview({ content }: { content: string }) {
  if (!content) return null;

  const lines = content.split("\n");
  const elements: React.ReactElement[] = [];
  let inCodeBlock = false;
  let codeContent = "";
  let codeKey = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith("```")) {
      if (inCodeBlock) {
        elements.push(
          <pre key={`code-${codeKey++}`} className="bg-black/30 rounded-lg p-3 my-2 overflow-x-auto text-xs text-green-300 font-mono">
            <code>{codeContent}</code>
          </pre>
        );
        codeContent = "";
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeContent += line + "\n";
      continue;
    }

    if (line.startsWith("### ")) {
      elements.push(<h3 key={i} className="text-base font-semibold text-white/90 mt-5 mb-2">{line.slice(4)}</h3>);
    } else if (line.startsWith("## ")) {
      elements.push(<h2 key={i} className="text-lg font-bold text-white mt-6 mb-2">{line.slice(3)}</h2>);
    } else if (line.startsWith("# ")) {
      elements.push(<h1 key={i} className="text-xl font-bold text-white mt-6 mb-3">{line.slice(2)}</h1>);
    } else if (line.startsWith("- ") || line.startsWith("* ")) {
      elements.push(<li key={i} className="text-white/70 ml-4 list-disc text-sm">{line.slice(2)}</li>);
    } else if (/^\d+\. /.test(line)) {
      elements.push(<li key={i} className="text-white/70 ml-4 list-decimal text-sm">{line.replace(/^\d+\. /, "")}</li>);
    } else if (line.startsWith("> ")) {
      elements.push(
        <blockquote key={i} className="border-l-2 border-orange-400/30 pl-3 py-1 my-1 text-sm text-white/60 italic">
          {line.slice(2)}
        </blockquote>
      );
    } else if (line.trim() === "") {
      elements.push(<div key={i} className="h-2" />);
    } else if (line.startsWith("---")) {
      elements.push(<hr key={i} className="border-white/5 my-3" />);
    } else if (line.startsWith("|")) {
      // Simple table detection
      if (i === 0 || !lines[i - 1].startsWith("|")) {
        elements.push(<div key={i} className="text-white/70 text-sm font-mono bg-white/[0.02] p-2 rounded my-1">{line}</div>);
      } else {
        elements.push(<div key={i} className="text-white/70 text-sm font-mono">{line}</div>);
      }
    } else {
      // Bold and inline code
      const processed = line
        .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
        .replace(/`(.*?)`/g, '<code class="bg-white/10 px-1 rounded text-orange-300 text-xs">$1</code>')
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a class="text-orange-400 hover:text-orange-300 underline">$1</a>');
      elements.push(
        <p key={i} className="text-white/70 text-sm leading-relaxed" dangerouslySetInnerHTML={{ __html: processed }} />
      );
    }
  }

  return <div className="space-y-0.5">{elements}</div>;
}

/* ============================================================
   Main Knowledge Page
   ============================================================ */

export default function KnowledgePage() {
  const [viewMode, setViewMode] = useState<"timeline" | "files">("timeline");
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [selectedPath, setSelectedPath] = useState<string>("");
  const [fileData, setFileData] = useState<FileContent | null>(null);
  const [editContent, setEditContent] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [loadingTree, setLoadingTree] = useState(false);
  const [loadingFile, setLoadingFile] = useState(false);
  const [saving, setSaving] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  /* ---- Load tree on mount ---- */
  useEffect(() => {
    if (viewMode === "files") {
      fetchTree();
    }
  }, [viewMode]);

  const fetchTree = async () => {
    setLoadingTree(true);
    try {
      const res = await fetch("/api/knowledge/list");
      if (res.ok) {
        const data = await res.json();
        setTree(data.tree ?? []);
      }
    } catch {
      // Offline fallback
    } finally {
      setLoadingTree(false);
    }
  };

  /* ---- Load file content ---- */
  const loadFile = useCallback(async (path: string) => {
    setLoadingFile(true);
    setSelectedPath(path);
    setIsEditing(false);
    try {
      const res = await fetch(`/api/knowledge/content?path=${encodeURIComponent(path)}`);
      if (res.ok) {
        const data: FileContent = await res.json();
        setFileData(data);
        setEditContent(data.content);
      } else {
        toast("无法加载文件", "error");
      }
    } catch {
      toast("加载失败，请检查网络", "error");
    } finally {
      setLoadingFile(false);
    }
  }, []);

  /* ---- Save content ---- */
  const handleSave = async () => {
    if (!selectedPath) return;
    setSaving(true);
    try {
      const res = await fetch("/api/knowledge/content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: selectedPath, content: editContent }),
      });
      if (res.ok) {
        toast("保存成功", "success");
        setIsEditing(false);
        // Refresh
        loadFile(selectedPath);
      } else {
        toast("保存失败", "error");
      }
    } catch {
      toast("保存失败，请检查网络", "error");
    } finally {
      setSaving(false);
    }
  };

  /* ---- Search filter ---- */
  const filteredTree = useMemo(() => {
    if (!searchQuery.trim()) return tree;

    const searchInTree = (nodes: TreeNode[]): TreeNode[] => {
      const result: TreeNode[] = [];
      for (const node of nodes) {
        if (node.type === "folder") {
          const filteredChildren = searchInTree(node.children ?? []);
          if (filteredChildren.length > 0) {
            result.push({ ...node, children: filteredChildren });
          }
        } else if (
          node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          node.path.toLowerCase().includes(searchQuery.toLowerCase())
        ) {
          result.push(node);
        }
      }
      return result;
    };

    return searchInTree(tree);
  }, [tree, searchQuery]);

  /* ---- Cancel editing ---- */
  const cancelEdit = () => {
    setIsEditing(false);
    if (fileData) {
      setEditContent(fileData.content);
    }
  };

  const toggleView = () => {
    setViewMode(viewMode === "timeline" ? "files" : "timeline");
    if (viewMode === "timeline") {
      // Switching to files mode
      fetchTree();
    }
  };

  /* ---- Render ---- */
  return (
    <div className="relative min-h-screen">
      <div className="bg-grid pointer-events-none fixed inset-0 z-0" />
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full bg-orange-500/10 blur-[120px]" />
        <div className="absolute -top-20 -right-20 w-[400px] h-[400px] rounded-full bg-blue-500/10 blur-[120px]" />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full bg-purple-500/8 blur-[120px]" />
      </div>

      <div className="relative z-10">
        {/* ---- View toggle header ---- */}
        <div className="max-w-7xl mx-auto px-4 pt-6 pb-2 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">知识库</h1>
            <div className="flex items-center gap-1 bg-white/5 rounded-lg p-0.5">
              <button
                onClick={() => setViewMode("timeline")}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  viewMode === "timeline"
                    ? "bg-orange-500/20 text-orange-300"
                    : "text-white/40 hover:text-white/70"
                }`}
              >
                <Layers className="h-3.5 w-3.5 inline mr-1" />
                九层体系
              </button>
              <button
                onClick={toggleView}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  viewMode === "files"
                    ? "bg-orange-500/20 text-orange-300"
                    : "text-white/40 hover:text-white/70"
                }`}
              >
                <FolderOpen className="h-3.5 w-3.5 inline mr-1" />
                文件管理
              </button>
            </div>
          </div>
        </div>

        {viewMode === "timeline" ? (
          /* ========== TIMELINE VIEW (original 9-layer content) ========== */
          <div className="max-w-3xl mx-auto px-4 py-6 sm:py-10">
            <div className="text-center mb-10">
              <Badge variant="secondary" className="mb-4 dark:bg-white/10 dark:text-gray-200 border-white/20">
                从0到爆款的完整知识金字塔
              </Badge>
              <h1 className="text-gradient text-3xl sm:text-4xl font-extrabold tracking-tight mb-3">
                九层知识体系
              </h1>
              <p className="text-muted-foreground text-base max-w-xl mx-auto">
                系统化构建爆款能力，底层逻辑 → 顶层运营
              </p>
            </div>

            {/* Vertical timeline */}
            <div className="relative flex gap-5">
              <div className="flex-shrink-0 w-[3px] rounded-full bg-gradient-to-b from-purple-500 via-blue-500 to-amber-500 absolute left-[27px] top-0 bottom-0 opacity-30" />

              {layers.map((layer, idx) => {
                const Icon = layer.icon;
                return (
                  <div key={layer.level} className="relative flex-1 pt-3 first:pt-0" style={{ marginTop: idx === 0 ? 0 : -8 }}>
                    <div className="absolute left-[20px] top-[14px] z-10 flex items-center justify-center">
                      <div className={`w-5 h-5 rounded-full border-2 dark:bg-gray-950 ${
                        idx < 4
                          ? "bg-white border-purple-400 shadow-[0_0_10px_rgba(168,85,247,.4)]"
                          : "bg-white border-gray-300 dark:border-gray-600"
                      }`} />
                    </div>

                    <div className={`
                      glass-card group rounded-xl p-4 border-l-4 border-l-${layer.color}
                      transition-all duration-300 hover:scale-[1.015] hover:-translate-y-0.5
                      ${layer.glowClass ? `${layer.glowClass} rounded-t-xl rounded-b-none` : ""}
                    `}>
                      <div className="flex items-center gap-4">
                        <div className="flex-shrink-0 w-11 h-11 rounded-full flex items-center justify-center dark:bg-white/5 ring-1 dark:ring-white/10 group-hover:dark:ring-white/20 transition">
                          <Icon className="w-5 h-5 dark:text-white/70 group-hover:text-white transition-colors" />
                        </div>
                        <div className="flex-shrink-0 w-11 h-11 rounded-full flex items-center justify-center text-xs font-bold dark:bg-white/5 dark:text-white/60 group-hover:bg-white/10 transition">
                          {layer.level}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-base font-semibold dark:text-white/90 group-hover:text-white transition">{layer.title}</h3>
                          <p className="text-sm text-muted-foreground">{layer.desc}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Quick links */}
            <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-4">
              {quickLinks.map((link) => {
                const Icon = link.icon;
                return (
                  <Link key={link.href} href={link.href} passHref>
                    <div className={`
                      glass-card rounded-xl p-5 ${link.glowClass} rounded-t-xl rounded-b-none
                      group cursor-pointer transition-all duration-300 hover:scale-[1.03] hover:-translate-y-1
                    `}>
                      <div className="flex flex-col items-center text-center gap-3">
                        <div className={`w-12 h-12 rounded-full dark:bg-white/5 flex items-center justify-center ${link.iconColor} group-hover:dark:bg-white/10 transition`}>
                          <Icon className="w-6 h-6" />
                        </div>
                        <div>
                          <div className="font-semibold dark:text-white/90 group-hover:text-white transition text-base">{link.title}</div>
                          <div className="text-sm text-muted-foreground mt-1">{link.desc}</div>
                        </div>
                        <div className="mt-auto w-full">
                          <Button variant="ghost" size="sm" className="w-full dark:text-white/50 dark:hover:text-white/90 dark:hover:bg-white/10">
                            进入 <ArrowRight className="ml-2 w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        ) : (
          /* ========== FILE MANAGEMENT VIEW ========== */
          <div className="max-w-7xl mx-auto px-4 py-4 flex gap-4" style={{ height: "calc(100vh - 120px)" }}>
            {/* ---- Left sidebar: Category tree ---- */}
            <div className={`
              ${sidebarOpen ? "w-64 shrink-0" : "w-0 overflow-hidden"}
              transition-all duration-300
            `}>
              <Card className="glass-card border-white/5 h-full flex flex-col overflow-hidden">
                <CardHeader className="pb-2 shrink-0">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm text-white/70 flex items-center gap-1.5">
                      <ListTree className="h-4 w-4 text-orange-400" />
                      文件浏览器
                    </CardTitle>
                    <button
                      onClick={() => setSidebarOpen(false)}
                      className="text-white/20 hover:text-white/50 transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Search */}
                  <div className="relative mt-2">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-white/30" />
                    <Input
                      placeholder="搜索文件..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-8 h-8 text-xs border-white/10 bg-white/[0.03] text-white placeholder:text-white/20 focus:border-orange-400/50"
                    />
                  </div>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto p-2">
                  {loadingTree ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-5 w-5 animate-spin text-orange-400" />
                    </div>
                  ) : filteredTree.length === 0 ? (
                    <div className="text-center py-8 text-white/30 text-xs">暂无文件</div>
                  ) : (
                    filteredTree.map((node) => (
                      <TreeItem
                        key={node.id}
                        node={node}
                        selectedPath={selectedPath}
                        depth={0}
                        onSelect={loadFile}
                      />
                    ))
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Sidebar collapse toggle when hidden */}
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="shrink-0 h-10 w-8 flex items-center justify-center rounded-lg border border-white/10
                  bg-white/[0.03] text-white/30 hover:text-white/60 hover:bg-white/10 transition-all"
              >
                <Menu className="h-4 w-4" />
              </button>
            )}

            {/* ---- Right content area ---- */}
            <div className="flex-1 min-w-0">
              {!selectedPath ? (
                /* Default empty state - show welcome */
                <Card className="glass-card border-white/5 h-full flex items-center justify-center">
                  <CardContent className="text-center py-12">
                    <div className="w-16 h-16 rounded-full bg-orange-500/10 flex items-center justify-center mx-auto mb-4">
                      <BookMarked className="h-8 w-8 text-orange-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">知识库文件管理</h3>
                    <p className="text-sm text-white/40 max-w-md">
                      在左侧选择一个文件来查看和编辑内容。支持方法论、模板库、专家库和提示词库的在线编辑。
                    </p>
                  </CardContent>
                </Card>
              ) : loadingFile ? (
                <Card className="glass-card border-white/5 h-full flex items-center justify-center">
                  <div className="flex flex-col items-center gap-2">
                    <Loader2 className="h-6 w-6 animate-spin text-orange-400" />
                    <p className="text-sm text-white/40">加载中...</p>
                  </div>
                </Card>
              ) : fileData ? (
                <Card className="glass-card border-white/5 h-full flex flex-col overflow-hidden">
                  {/* File header */}
                  <CardHeader className="pb-3 shrink-0">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div>
                        <CardTitle className="text-base text-white flex items-center gap-2">
                          <FileText className="h-4 w-4 text-orange-400" />
                          {fileData.meta.fileName}
                        </CardTitle>
                        <div className="flex items-center gap-3 mt-1.5 text-[10px] text-white/30 flex-wrap">
                          <span className="inline-flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {new Date(fileData.meta.modified).toLocaleString("zh-CN")}
                          </span>
                          <span className="inline-flex items-center gap-1">
                            <FileText className="h-3 w-3" />
                            {fileData.meta.wordCount} 字
                          </span>
                          <span className="inline-flex items-center gap-1">
                            <Tag className="h-3 w-3" />
                            {fileData.meta.tags.slice(0, 3).join(", ")}
                          </span>
                          <Badge
                            variant="outline"
                            className={`text-[9px] px-1.5 py-0 ${
                              CATEGORY_BADGE_COLORS[selectedPath.split("/")[0]] ?? "border-white/10 text-white/30"
                            }`}
                          >
                            {CATEGORY_LABELS[selectedPath.split("/")[0]] ?? selectedPath.split("/")[0]}
                          </Badge>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {isEditing ? (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={cancelEdit}
                              className="border-white/10 text-white/50 hover:bg-white/10 hover:text-white h-8 text-xs"
                            >
                              <X className="h-3.5 w-3.5 mr-1" />取消
                            </Button>
                            <Button
                              size="sm"
                              onClick={handleSave}
                              disabled={saving}
                              className="bg-orange-500/80 hover:bg-orange-500 text-white h-8 text-xs"
                            >
                              {saving ? (
                                <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
                              ) : (
                                <Save className="h-3.5 w-3.5 mr-1" />
                              )}
                              {saving ? "保存中..." : "保存"}
                            </Button>
                          </>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setIsEditing(true)}
                            className="border-white/10 text-white/50 hover:bg-white/10 hover:text-white h-8 text-xs"
                          >
                            <FileEdit className="h-3.5 w-3.5 mr-1" />编辑
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardHeader>

                  {/* File content */}
                  <CardContent className="flex-1 overflow-y-auto p-0">
                    {isEditing ? (
                      <div className="h-full flex flex-col">
                        {/* Edit/Preview tabs */}
                        <div className="flex items-center gap-1 px-4 py-2 border-b border-white/5 bg-white/[0.02]">
                          <button
                            className="px-2.5 py-1 rounded text-xs font-medium bg-orange-500/15 text-orange-300"
                          >
                            <FileEdit className="h-3 w-3 inline mr-1" />编辑
                          </button>
                        </div>
                        <textarea
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          className="flex-1 w-full bg-black/20 text-white/80 text-sm font-mono p-4 resize-none
                            border-0 outline-none focus:ring-0 placeholder:text-white/20"
                          spellCheck={false}
                        />
                      </div>
                    ) : (
                      <div className="p-5">
                        <MarkdownPreview content={fileData.content} />
                      </div>
                    )}
                  </CardContent>
                </Card>
              ) : (
                <Card className="glass-card border-white/5 h-full flex items-center justify-center">
                  <div className="text-center py-12">
                    <p className="text-sm text-white/30">文件加载失败</p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => loadFile(selectedPath)}
                      className="mt-3 border-white/10 text-white/50 hover:bg-white/10 hover:text-white"
                    >
                      <RefreshCw className="h-3.5 w-3.5 mr-1" />重试
                    </Button>
                  </div>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
