"use client";

import { useState, useEffect, useRef, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface TransitionProps {
  children: ReactNode;
  className?: string;
  /** 动画持续时间（毫秒），默认 300 */
  duration?: number;
  /** 进入动画类型 */
  animation?: "fade-in" | "fade-in-up" | "fade-in-down" | "scale-in";
  /** 是否在初始渲染时应用动画 */
  animateOnMount?: boolean;
  /** 触发重新动画的 key，每次改变都会重播动画 */
  trigger?: string | number;
}

const ANIMATION_CLASSES: Record<string, string> = {
  "fade-in": "opacity-0",
  "fade-in-up": "opacity-0 translate-y-4",
  "fade-in-down": "opacity-0 -translate-y-4",
  "scale-in": "opacity-0 scale-95",
};

/**
 * Transition — 页面/内容切换过渡动画
 *
 * 包裹子组件，在挂载或 trigger 变化时播放进入动画。
 * 默认使用 fade-in-up 效果。
 *
 * @example
 * ```tsx
 * // 简单的淡入
 * <Transition>
 *   <MyContent />
 * </Transition>
 *
 * // 改变 trigger 时重播动画
 * <Transition key={page} trigger={page} animation="scale-in">
 *   <PageContent page={page} />
 * </Transition>
 * ```
 */
export function Transition({
  children,
  className,
  duration = 300,
  animation = "fade-in-up",
  animateOnMount = true,
  trigger,
}: TransitionProps) {
  const [mounted, setMounted] = useState(false);
  const [visible, setVisible] = useState(!animateOnMount);
  const prevTrigger = useRef(trigger);

  useEffect(() => {
    if (!animateOnMount) {
      setVisible(true);
      return;
    }

    // trigger 变化时重播
    if (mounted && trigger !== prevTrigger.current) {
      prevTrigger.current = trigger;
      setVisible(false);
      const timer = setTimeout(() => setVisible(true), 20);
      return () => clearTimeout(timer);
    }

    // 首次挂载
    setMounted(true);
    const timer = setTimeout(() => setVisible(true), 20);
    return () => clearTimeout(timer);
  }, [trigger, animateOnMount, mounted]);

  // 首次不显示动画
  if (animateOnMount && !mounted) {
    return <div className={className}>{children}</div>;
  }

  return (
    <div
      className={cn(
        "transition-all ease-out",
        !visible && ANIMATION_CLASSES[animation],
        visible && "opacity-100 translate-y-0 scale-100",
        className
      )}
      style={{ transitionDuration: `${duration}ms` }}
    >
      {children}
    </div>
  );
}

/**
 * StaggerChildren — 子元素逐条进入动画容器
 *
 * 每个子元素依次延迟出现，适合列表、卡片组等场景。
 *
 * @example
 * ```tsx
 * <StaggerChildren>
 *   <Card key={1} />
 *   <Card key={2} />
 *   <Card key={3} />
 * </StaggerChildren>
 * ```
 */
export function StaggerChildren({
  children,
  className,
  staggerDelay = 80,
  animateOnMount = false,
}: {
  children: ReactNode;
  className?: string;
  staggerDelay?: number;
  animateOnMount?: boolean;
}) {
  const [mounted, setMounted] = useState(animateOnMount ? false : true);

  useEffect(() => {
    if (animateOnMount) {
      setMounted(true);
    }
  }, [animateOnMount]);

  const childrenArray = Array.isArray(children) ? children : [children];

  return (
    <div className={className}>
      {childrenArray.map((child, index) => {
        const delay = mounted ? index * staggerDelay : 0;
        return (
          <div
            key={index}
            className="transition-all ease-out"
            style={{
              opacity: mounted ? 1 : 0,
              transform: mounted ? "translateY(0)" : "translateY(1rem)",
              transitionDuration: "0.4s",
              transitionDelay: `${delay}ms`,
            }}
          >
            {child}
          </div>
        );
      })}
    </div>
  );
}
