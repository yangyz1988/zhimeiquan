"use client";

import { useState, useRef, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Smartphone, Monitor, RotateCw, Hash, Sparkles,
  Quote, Eye, Heart, MessageSquare, Share2, Play,
  Download, Maximize2, Copy, Check, X,
} from "lucide-react";
import { toast } from "@/components/toaster";

/* ============================================================
   Types
   ============================================================ */

interface PreviewContent {
  titles: string[];
  script: string;
  tags: string[];
  hook: string;
}

interface PlatformPreviewProps {
  content?: PreviewContent;
  platforms?: string[];
}

/* ============================================================
   Platform config
   ============================================================ */

interface PlatformConfig {
  id: string;
  label: string;
  color: string;
  bgGradient: string;
  icon: string;
  aspectRatio: string;
  orientation: "vertical" | "horizontal";
  mockupWidth: string;
  mockupHeight: string;
}

const PLATFORM_CONFIGS: Record<string, PlatformConfig> = {
  douyin: {
    id: "douyin", label: "抖音", color: "#f97316",
    bgGradient: "bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900",
    icon: "🎵", aspectRatio: "9:16", orientation: "vertical",
    mockupWidth: "w-[200px]", mockupHeight: "h-[356px]",
  },
  xiaohongshu: {
    id: "xiaohongshu", label: "小红书", color: "#ec4899",
    bgGradient: "bg-gradient-to-b from-pink-950/80 via-gray-900 to-gray-900",
    icon: "📕", aspectRatio: "3:4", orientation: "vertical",
    mockupWidth: "w-[240px]", mockupHeight: "h-[320px]",
  },
  bilibili: {
    id: "bilibili", label: "B站", color: "#3b82f6",
    bgGradient: "bg-gradient-to-b from-blue-950/60 via-gray-900 to-gray-900",
    icon: "📺", aspectRatio: "16:9", orientation: "horizontal",
    mockupWidth: "w-[340px]", mockupHeight: "h-[192px]",
  },
  wechat: {
    id: "wechat", label: "公众号", color: "#22c55e",
    bgGradient: "bg-gradient-to-b from-green-950/60 via-gray-900 to-gray-900",
    icon: "💬", aspectRatio: "long-form", orientation: "horizontal",
    mockupWidth: "w-[340px]", mockupHeight: "h-[260px]",
  },
};

/* ============================================================
   Sub-components
   ============================================================ */

/** Phone mockup frame */
function PhoneFrame({ children, active }: { children: React.ReactNode; active: boolean }) {
  return (
    <div className={`
      relative rounded-[24px] border-2 overflow-hidden transition-all duration-300
      ${active ? "border-white/20 shadow-[0_0_30px_rgba(249,115,22,0.15)]" : "border-white/10"}
      bg-gray-900
    `}
      style={{ width: "240px", height: "420px" }}
    >
      {/* Notch */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[100px] h-5 bg-gray-900 rounded-b-xl z-10 flex items-center justify-center gap-1.5">
        <div className="w-2 h-2 rounded-full bg-gray-700" />
        <div className="w-12 h-1.5 rounded-full bg-gray-800" />
      </div>
      {/* Screen */}
      <div className="h-full w-full pt-5 overflow-hidden">
        {children}
      </div>
      {/* Home indicator */}
      <div className="absolute bottom-1 left-1/2 -translate-x-1/2 w-[100px] h-1 rounded-full bg-white/20" />
    </div>
  );
}

/** Desktop mockup frame */
function DesktopFrame({ children, active }: { children: React.ReactNode; active: boolean }) {
  return (
    <div className={`
      rounded-lg border overflow-hidden transition-all duration-300
      ${active ? "border-white/20 shadow-[0_0_30px_rgba(249,115,22,0.15)]" : "border-white/10"}
      bg-gray-900
    `}
      style={{ width: "100%", maxWidth: "400px", height: "300px" }}
    >
      {/* Title bar */}
      <div className="flex items-center gap-1.5 px-3 py-2 bg-gray-800/80 border-b border-white/5">
        <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
        <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
        <div className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
        <div className="ml-3 flex-1 max-w-[180px]">
          <div className="h-2 rounded-full bg-white/10 mx-auto" style={{ width: "60%" }} />
        </div>
      </div>
      {/* Content */}
      <div className="h-full overflow-hidden">
        {children}
      </div>
    </div>
  );
}

/* ============================================================
   Platform Previews
   ============================================================ */

/** Douyin Preview - 9:16 vertical short video card */
function DouyinPreview({ content }: { content: PreviewContent }) {
  const primaryTitle = content.titles[0] ?? "标题";
  const secondaryTitle = content.titles[1];
  const tags = content.tags.slice(0, 4);
  const hook = content.hook || content.script.slice(0, 60) + "...";

  return (
    <div className="h-full flex flex-col">
      {/* Cover area with gradient */}
      <div className="flex-1 bg-gradient-to-b from-orange-900/30 via-purple-900/20 to-gray-900 flex items-center justify-center relative">
        <div className="text-center px-4">
          <div className="w-14 h-14 rounded-full bg-orange-500/20 flex items-center justify-center mx-auto mb-3">
            <Play className="h-6 w-6 text-orange-400" fill="currentColor" />
          </div>
          <h3 className="text-white font-bold text-sm leading-tight mb-1 line-clamp-2">{primaryTitle}</h3>
          {secondaryTitle && (
            <p className="text-white/50 text-[10px] line-clamp-1">{secondaryTitle}</p>
          )}
        </div>
        {/* Play button overlay */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-12 h-12 rounded-full bg-white/10 backdrop-blur flex items-center justify-center">
            <Play className="h-5 w-5 text-white/70 ml-0.5" fill="currentColor" />
          </div>
        </div>
      </div>

      {/* Bottom info bar */}
      <div className="px-3 py-2 bg-black/40">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <div className="w-5 h-5 rounded-full bg-orange-500/30 flex items-center justify-center text-[8px]">AI</div>
            <span className="text-[10px] text-white/60">智媒圈</span>
          </div>
          <div className="flex items-center gap-2">
            <Heart className="h-3 w-3 text-white/40" />
            <span className="text-[9px] text-white/40">1.2w</span>
          </div>
        </div>
        <p className="text-[9px] text-white/50 mt-1 line-clamp-1">{hook}</p>
        {tags.length > 0 && (
          <div className="flex gap-1 mt-1 flex-wrap">
            {tags.map((tag, i) => (
              <span key={i} className="text-[8px] text-orange-300/70">#{tag}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/** Xiaohongshu Preview - 3:4 vertical card */
function XiaohongshuPreview({ content }: { content: PreviewContent }) {
  const title = content.titles[0] ?? "标题";
  const bodyPreview = content.script.slice(0, 120) + (content.script.length > 120 ? "..." : "");

  return (
    <div className="h-full flex flex-col">
      {/* Image area */}
      <div className="flex-[3] bg-gradient-to-br from-pink-800/30 via-rose-900/20 to-gray-900 flex items-center justify-center">
        <div className="text-center px-5">
          <p className="text-white font-bold text-sm leading-snug mb-2 line-clamp-3">
            {title}
          </p>
          <div className="flex items-center justify-center gap-3 text-[9px] text-white/40">
            <span className="flex items-center gap-1"><Heart className="h-2.5 w-2.5" /> 2.3w</span>
            <span className="flex items-center gap-1"><MessageSquare className="h-2.5 w-2.5" /> 856</span>
          </div>
        </div>
      </div>

      {/* Content area */}
      <div className="flex-[2] px-3 py-2 bg-white/[0.03]">
        <div className="flex items-center gap-1.5 mb-1.5">
          <div className="w-4 h-4 rounded-full bg-pink-400/30 flex items-center justify-center text-[6px]">X</div>
          <span className="text-[9px] text-white/50">小红书博主</span>
          <span className="text-[7px] text-white/20 ml-auto">3小时前</span>
        </div>
        <p className="text-[10px] text-white/70 leading-relaxed line-clamp-4">
          {bodyPreview}
        </p>
        <div className="flex gap-1 mt-1.5 flex-wrap">
          {content.tags.slice(0, 3).map((tag, i) => (
            <span key={i} className="text-[8px] text-pink-300/60">#{tag}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

/** Bilibili Preview - 16:9 horizontal card */
function BilibiliPreview({ content }: { content: PreviewContent }) {
  const title = content.titles[0] ?? "标题";
  const desc = content.script.slice(0, 100) + (content.script.length > 100 ? "..." : "");

  return (
    <div className="h-full flex">
      {/* Video thumbnail */}
      <div className="w-2/5 bg-gradient-to-br from-blue-800/30 to-gray-900 relative flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center mx-auto mb-1">
            <Play className="h-4 w-4 text-blue-400" fill="currentColor" />
          </div>
          <p className="text-[8px] text-white/30">12:34</p>
        </div>
        {/* Progress bar */}
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-white/10">
          <div className="h-full w-3/5 bg-blue-400/50 rounded-r" />
        </div>
        {/* Duration badge */}
        <div className="absolute bottom-1 right-1 bg-black/70 px-1 rounded text-[8px] text-white/60">12:34</div>
      </div>

      {/* Info panel */}
      <div className="flex-1 px-2.5 py-2 flex flex-col">
        <h3 className="text-[11px] text-white font-medium leading-snug line-clamp-2 mb-1">{title}</h3>
        <p className="text-[8px] text-white/40 line-clamp-2 flex-1">{desc}</p>
        <div className="flex items-center justify-between mt-auto">
          <div className="flex items-center gap-1">
            <div className="w-3.5 h-3.5 rounded-full bg-blue-400/30 flex items-center justify-center text-[5px]">B</div>
            <span className="text-[8px] text-white/40">UP主</span>
          </div>
          <div className="flex items-center gap-2 text-[8px] text-white/30">
            <span>35.2w播放</span>
            <span>1.8w赞</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/** WeChat Official Account Preview - long-form article */
function WechatPreview({ content }: { content: PreviewContent }) {
  const title = content.titles[0] ?? "标题";
  const bodyExcerpt = content.script.slice(0, 200) + (content.script.length > 200 ? "..." : "");

  return (
    <div className="h-full overflow-y-auto p-3 bg-gray-900">
      {/* Author bar */}
      <div className="flex items-center gap-2 mb-2">
        <div className="w-6 h-6 rounded-full bg-green-500/30 flex items-center justify-center text-[7px] text-green-400">W</div>
        <div>
          <p className="text-[9px] text-white/60 font-medium">智媒圈官方</p>
          <p className="text-[7px] text-white/20">原创 · 2026年6月</p>
        </div>
      </div>

      {/* Title */}
      <h2 className="text-sm font-bold text-white leading-snug mb-2">{title}</h2>

      {/* Subtitle */}
      {content.titles[1] && (
        <p className="text-[10px] text-white/40 mb-2">{content.titles[1]}</p>
      )}

      {/* Body preview */}
      <div className="text-[10px] text-white/60 leading-relaxed mb-3 space-y-1">
        <p>{bodyExcerpt}</p>
      </div>

      {/* Tags */}
      <div className="flex gap-1 flex-wrap">
        {content.tags.slice(0, 3).map((tag, i) => (
          <span key={i} className="text-[8px] text-green-400/50">#{tag}</span>
        ))}
      </div>

      {/* Engagement bar */}
      <div className="flex items-center gap-3 mt-2 pt-2 border-t border-white/5 text-[8px] text-white/30">
        <span className="flex items-center gap-0.5"><Eye className="h-2.5 w-2.5" /> 1.2w</span>
        <span className="flex items-center gap-0.5"><Heart className="h-2.5 w-2.5" /> 88</span>
        <span className="flex items-center gap-0.5"><MessageSquare className="h-2.5 w-2.5" /> 12</span>
      </div>
    </div>
  );
}

/* ============================================================
   Main Component
   ============================================================ */

export function PlatformPreview({ content, platforms }: PlatformPreviewProps) {
  const [activeOrientation, setActiveOrientation] = useState<"mobile" | "desktop">("mobile");
  const [activePlatform, setActivePlatform] = useState<string>("douyin");
  const [fullscreen, setFullscreen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [shareCopied, setShareCopied] = useState(false);
  const previewRef = useRef<HTMLDivElement>(null);

  const handleDownload = async () => {
    try {
      toast("正在导出预览图片...", "success");
      // Canvas-based screenshot export
      const canvas = document.createElement("canvas");
      const svgEl = previewRef.current?.querySelector("svg");
      if (svgEl) {
        const svgData = new XMLSerializer().serializeToString(svgEl);
        const img = new Image();
        img.onload = () => {
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext("2d");
          ctx?.drawImage(img, 0, 0);
          const link = document.createElement("a");
          link.download = "preview.png";
          link.href = canvas.toDataURL("image/png");
          link.click();
          toast("预览已下载");
        };
        img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svgData)));
      } else {
        toast("没有可导出的内容", "error");
      }
    } catch {
      toast("导出失败", "error");
    }
  };

  const handleShare = () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
      setShareCopied(true);
      toast("预览链接已复制到剪贴板");
      setTimeout(() => setShareCopied(false), 2000);
    }).catch(() => {
      toast("复制链接失败", "error");
    });
  };

  const defaultContent: PreviewContent = {
    titles: ["AI时代普通人如何抓住这波红利", "3个你必须知道的底层逻辑"],
    script: "大家好，今天我们来聊一个所有人都关心的话题：AI时代普通人到底还有没有机会？\n\n很多人觉得AI太遥远，是大公司、技术专家的游戏。但事实恰恰相反——AI正在创造前所未有的普通人逆袭机会。\n\n为什么？因为AI降低了内容创作的门槛，让每个人都有机会用专业级别的工具创作内容。你不需要会写代码，不需要懂算法，只需要一个好想法和执行力。\n\n接下来我给大家分享3个普通人可以立刻上手的AI变现路径…",
    tags: ["AI", "副业", "自媒体", "赚钱", "认知", "成长"],
    hook: "AI时代普通人还有机会吗？答案是：有，而且比任何时候都大",
  };

  const previewContent = content ?? defaultContent;
  const activePlatforms = platforms ?? ["douyin", "xiaohongshu", "bilibili", "wechat"];

  // Filter platforms by orientation
  const verticalPlatforms = activePlatforms.filter(
    (p) => PLATFORM_CONFIGS[p]?.orientation === "vertical"
  );
  const horizontalPlatforms = activePlatforms.filter(
    (p) => PLATFORM_CONFIGS[p]?.orientation === "horizontal"
  );

  const displayPlatforms = activeOrientation === "mobile" ? verticalPlatforms : horizontalPlatforms;
  const effectiveActive = displayPlatforms.includes(activePlatform) ? activePlatform : (displayPlatforms[0] ?? activePlatforms[0]);

  const empty = !content;

  return (
    <Card className={`glass-card border-white/5 overflow-hidden ${empty ? "" : "glow-orange"}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <CardTitle className="text-base text-white flex items-center gap-2">
            <Eye className="h-4 w-4 text-orange-400" />
            平台预览
            {empty && (
              <Badge variant="outline" className="text-[9px] border-white/10 text-white/30">
                示例数据
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center gap-2 flex-wrap">
            {/* Action buttons */}
            <button
              onClick={handleShare}
              className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium transition-all text-white/40 hover:text-white/70 hover:bg-white/5"
              title="分享预览链接"
            >
              {shareCopied ? (
                <Check className="h-3 w-3" />
              ) : (
                <Share2 className="h-3 w-3" />
              )}
              {shareCopied ? "已复制" : "分享"}
            </button>
            <button
              onClick={handleDownload}
              className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium transition-all text-white/40 hover:text-white/70 hover:bg-white/5"
              title="下载预览为PNG"
            >
              <Download className="h-3 w-3" />
              下载
            </button>
            <button
              onClick={() => setFullscreen(!fullscreen)}
              className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium transition-all text-white/40 hover:text-white/70 hover:bg-white/5"
              title={fullscreen ? "退出全屏" : "全屏查看"}
            >
              {fullscreen ? <X className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}
              {fullscreen ? "退出" : "全屏"}
            </button>
            <div className="flex items-center gap-1 bg-white/5 rounded-lg p-0.5">
            <button
              onClick={() => { setActiveOrientation("mobile"); setActivePlatform(verticalPlatforms[0] ?? "douyin"); }}
              className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-all flex items-center gap-1 ${
                activeOrientation === "mobile"
                  ? "bg-orange-500/20 text-orange-300"
                  : "text-white/40 hover:text-white/70"
              }`}
            >
              <Smartphone className="h-3 w-3" />
              竖版
            </button>
            <button
              onClick={() => { setActiveOrientation("desktop"); setActivePlatform(horizontalPlatforms[0] ?? "bilibili"); }}
              className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-all flex items-center gap-1 ${
                activeOrientation === "desktop"
                  ? "bg-orange-500/20 text-orange-300"
                  : "text-white/40 hover:text-white/70"
              }`}
            >
              <Monitor className="h-3 w-3" />
              横版
            </button>
          </div>
        </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Platform selector tabs */}
        <div className="flex gap-1.5 mb-4 flex-wrap">
          {displayPlatforms.map((pid) => {
            const cfg = PLATFORM_CONFIGS[pid];
            if (!cfg) return null;
            const isActive = effectiveActive === pid;
            return (
              <button
                key={pid}
                onClick={() => setActivePlatform(pid)}
                className={`
                  flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                  ${isActive
                    ? "bg-white/10 text-white border border-white/15"
                    : "text-white/40 hover:text-white/70 hover:bg-white/5 border border-transparent"
                  }
                `}
              >
                <span style={{ color: cfg.color }}>{cfg.icon}</span>
                {cfg.label}
              </button>
            );
          })}
        </div>

        {/* Preview area */}
        <div
          ref={previewRef}
          className={`flex justify-center transition-all duration-300 ${
            fullscreen ? "fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-8" : ""
          }`}
          onClick={() => fullscreen && setFullscreen(false)}
        >
          {effectiveActive === "douyin" && (
            <PhoneFrame active={true}>
              <DouyinPreview content={previewContent} />
            </PhoneFrame>
          )}
          {effectiveActive === "xiaohongshu" && (
            <PhoneFrame active={true}>
              <XiaohongshuPreview content={previewContent} />
            </PhoneFrame>
          )}
          {effectiveActive === "bilibili" && (
            <DesktopFrame active={true}>
              <BilibiliPreview content={previewContent} />
            </DesktopFrame>
          )}
          {effectiveActive === "wechat" && (
            <DesktopFrame active={true}>
              <WechatPreview content={previewContent} />
            </DesktopFrame>
          )}
        </div>

        {/* Content stats */}
        {previewContent && (
          <div className="mt-4 grid grid-cols-4 gap-2">
            <div className="bg-white/[0.03] rounded-lg p-2 text-center">
              <div className="text-[9px] text-white/30">标题</div>
              <div className="text-xs font-medium text-white mt-0.5">{previewContent.titles.length}</div>
            </div>
            <div className="bg-white/[0.03] rounded-lg p-2 text-center">
              <div className="text-[9px] text-white/30">标签</div>
              <div className="text-xs font-medium text-white mt-0.5">{previewContent.tags.length}</div>
            </div>
            <div className="bg-white/[0.03] rounded-lg p-2 text-center">
              <div className="text-[9px] text-white/30">字数</div>
              <div className="text-xs font-medium text-white mt-0.5">{previewContent.script.length}</div>
            </div>
            <div className="bg-white/[0.03] rounded-lg p-2 text-center">
              <div className="text-[9px] text-white/30">钩子</div>
              <div className="text-xs font-medium text-white mt-0.5">{previewContent.hook ? "有" : "无"}</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default PlatformPreview;
