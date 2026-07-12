"use client";

import { Component, type ReactNode } from "react";
import { AlertTriangle, RefreshCw, Bug } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * ErrorBoundary — 增强版错误边界组件
 *
 * 特性:
 * - 玻璃卡片风格错误展示
 * - "重试"按钮重置错误状态
 * - 开发模式下显示详细错误堆栈
 * - 自动 console.error 日志记录
 * - 支持自定义 fallback
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // 记录错误到控制台，方便调试
    console.error("[ErrorBoundary] 捕获到错误:", error);
    console.error("[ErrorBoundary] 组件堆栈:", errorInfo.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      const isDev = process.env.NODE_ENV === "development";

      return (
        <div className="flex min-h-[300px] items-center justify-center p-6">
          <div className="glass-card w-full max-w-md border border-white/10 p-8 text-center transition-all duration-300">
            {/* 错误图标 */}
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10">
              <AlertTriangle className="h-8 w-8 text-red-400" />
            </div>

            {/* 主标题 */}
            <h2 className="mb-2 text-xl font-semibold text-white">
              页面出错了
            </h2>

            {/* 错误描述 */}
            <p className="mb-2 text-sm text-white/50">
              {this.state.error?.message || "发生了未知错误，请稍后重试"}
            </p>

            {/* 开发模式：详细错误信息 */}
            {isDev && this.state.error && (
              <details className="group mb-4 text-left">
                <summary className="flex cursor-pointer items-center gap-1 text-xs text-white/40 hover:text-white/60 transition-colors">
                  <Bug className="h-3 w-3" />
                  错误详情（开发模式）
                </summary>
                <pre className="mt-2 max-h-40 overflow-auto rounded-lg bg-black/40 p-3 text-xs text-red-300/80 whitespace-pre-wrap break-all">
                  {this.state.error.stack || this.state.error.message}
                </pre>
              </details>
            )}

            {/* 重试按钮 */}
            <Button
              onClick={this.handleReset}
              variant="outline"
              className="border-white/10 text-white/70 hover:text-white hover:bg-white/10 transition-all duration-300"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              重试
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
