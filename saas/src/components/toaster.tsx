"use client";

import { useState, useEffect, useCallback, type ReactNode } from "react";
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type ToastType = "success" | "error" | "info" | "warning";

interface ToastAction {
  label: string;
  onClick: () => void;
}

interface Toast {
  id: number;
  message: string;
  type: ToastType;
  action?: ToastAction;
  /** 自定义自动关闭时间（毫秒），默认 4000 */
  duration?: number;
}

type ToastInput = Omit<Toast, "id">;

let listeners: ((toast: Toast) => void)[] = [];

/**
 * toast — 全局消息提示
 *
 * 在任意组件中调用即可弹出通知。
 *
 * @example
 * ```tsx
 * toast("保存成功", "success");
 * toast("即将删除", "warning", { label: "撤销", onClick: undoDelete });
 * ```
 */
export function toast(
  message: string,
  type: ToastType = "info",
  action?: ToastAction,
  duration?: number
) {
  const t: Toast = { id: Date.now() + Math.random(), message, type, action, duration };
  listeners.forEach((l) => l(t));
}

// 便捷方法
toast.success = (message: string, action?: ToastAction) => toast(message, "success", action);
toast.error = (message: string, action?: ToastAction) => toast(message, "error", action);
toast.warning = (message: string, action?: ToastAction) => toast(message, "warning", action);
toast.info = (message: string, action?: ToastAction) => toast(message, "info", action);

interface IconConfig {
  icon: typeof CheckCircle2;
  bgClass: string;
  iconClass: string;
  borderClass: string;
}

const TYPE_CONFIG: Record<ToastType, IconConfig> = {
  success: {
    icon: CheckCircle2,
    bgClass: "bg-green-500/10",
    iconClass: "text-green-400",
    borderClass: "border-green-500/30",
  },
  error: {
    icon: AlertCircle,
    bgClass: "bg-red-500/10",
    iconClass: "text-red-400",
    borderClass: "border-red-500/30",
  },
  info: {
    icon: Info,
    bgClass: "bg-blue-500/10",
    iconClass: "text-blue-400",
    borderClass: "border-blue-500/30",
  },
  warning: {
    icon: AlertTriangle,
    bgClass: "bg-yellow-500/10",
    iconClass: "text-yellow-400",
    borderClass: "border-yellow-500/30",
  },
};

export function Toaster() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const listener = (t: Toast) => {
      setToasts((prev) => [...prev, t]);
      const duration = t.duration ?? 4000;
      setTimeout(() => {
        setToasts((prev) => prev.filter((x) => x.id !== t.id));
      }, duration);
    };
    listeners.push(listener);
    return () => {
      listeners = listeners.filter((l) => l !== listener);
    };
  }, []);

  const remove = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <div className="fixed right-4 top-20 z-50 flex flex-col gap-2 pointer-events-none" aria-live="polite">
      {toasts.map((t) => {
        const config = TYPE_CONFIG[t.type];
        const Icon = config.icon;

        return (
          <div
            key={t.id}
            className={cn(
              "pointer-events-auto flex items-center gap-3 rounded-xl border px-4 py-3 shadow-lg",
              "bg-black/70 backdrop-blur-xl",
              config.borderClass,
              "animate-in slide-in-from-right transition-all duration-300",
              "min-w-[280px] max-w-[380px]"
            )}
          >
            {/* 图标 */}
            <div className={cn("flex h-8 w-8 items-center justify-center rounded-full", config.bgClass)}>
              <Icon className={cn("h-4 w-4", config.iconClass)} />
            </div>

            {/* 消息内容 */}
            <span className="flex-1 text-sm text-white/90">{t.message}</span>

            {/* 操作按钮 */}
            {t.action && (
              <button
                onClick={t.action.onClick}
                className="whitespace-nowrap rounded-md px-2 py-1 text-xs font-medium text-orange-400 hover:text-orange-300 hover:bg-white/10 transition-colors"
              >
                {t.action.label}
              </button>
            )}

            {/* 关闭按钮 */}
            <button
              onClick={() => remove(t.id)}
              className="flex h-5 w-5 items-center justify-center rounded-full text-white/30 hover:text-white/70 hover:bg-white/10 transition-all"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
