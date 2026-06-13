"use client";

import { Badge, type BadgeProps } from "@/components/ui/badge";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { type KeyboardEvent, type forwardRef } from "react";

/** 可点击的 Badge 样式变体 */
const clickBadgeVariants = cva(
  "transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:ring-offset-2 focus-visible:ring-offset-transparent cursor-pointer select-none",
  {
    variants: {
      variant: {
        default: "bg-white/10 border border-white/10 text-white/50 hover:bg-white/20 hover:text-white",
        outline: "border-white/15 text-white/40 hover:bg-white/5 hover:text-white/60",
        glowOrange: "bg-orange-500/80 text-white shadow-[0_0_12px_rgba(249,115,22,0.4)]",
        glowBlue: "bg-blue-500/80 text-white shadow-[0_0_12px_rgba(59,130,246,0.4)]",
        glowPurple: "bg-purple-500/80 text-white shadow-[0_0_12px_rgba(168,85,247,0.4)]",
        glowGreen: "bg-green-500/80 text-white shadow-[0_0_12px_rgba(34,197,94,0.4)]",
      },
    },
    defaultVariants: {
      variant: "outline",
    },
  },
);

export interface ClickableBadgeProps
  extends Omit<BadgeProps, "variant">,
    VariantProps<typeof clickBadgeVariants> {
  /** 是否处于激活/选中状态 */
  active?: boolean;
  /** 点击回调 */
  onClick: () => void;
  /** ARIA 标签 */
  ariaLabel?: string;
}

/**
 * ClickableBadge — 无障碍友好的可点击 Badge
 * 支持键盘 Enter/Space 操作，有 aria-pressed 状态
 */
export const ClickableBadge = forwardRef<HTMLDivElement, ClickableBadgeProps>(
  ({ className, active, variant, onClick, ariaLabel, ...props }, ref) => {
    const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onClick();
      }
    };

    return (
      <div
        ref={ref}
        role="button"
        tabIndex={0}
        aria-pressed={active}
        aria-label={ariaLabel}
        className={cn(
          clickBadgeVariants({ variant: active ? `glow${variant.charAt(0).toUpperCase() + variant.slice(1)}` : variant }),
          className,
        )}
        onClick={onClick}
        onKeyDown={handleKeyDown}
        {...props}
      />
    );
  },
);
