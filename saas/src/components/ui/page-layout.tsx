"use client";

interface PageBackgroundProps {
  color1?: string;
  color2?: string;
  size1?: string;
  size2?: string;
}

/**
 * PageBackground — 全屏装饰性背景光晕
 * 所有页面的统一背景层，避免重复代码
 */
export function PageBackground({
  color1 = "bg-orange-500/[0.05]",
  color2 = "bg-blue-500/[0.04]",
  size1 = "w-[500px] h-[500px]",
  size2 = "w-[400px] h-[400px]",
}: PageBackgroundProps) {
  return (
    <div className="pointer-events-none fixed inset-0 z-0">
      <div className={`absolute -top-40 right-1/4 ${size1} rounded-full ${color1} blur-[120px]`} />
      <div className={`absolute bottom-0 left-1/3 ${size2} rounded-full ${color2} blur-[100px]`} />
    </div>
  );
}

/**
 * SectionHeading — 统一的章节标题组件
 * 所有页面的 section 标题统一使用
 */
interface SectionHeadingProps {
  title: string;
  subtitle?: string;
  gradientClass?: string;
}

export function SectionHeading({ title, subtitle, gradientClass }: SectionHeadingProps) {
  return (
    <div className="text-center space-y-2">
      <h2 className={`text-3xl font-bold sm:text-4xl ${gradientClass || "text-white"}`}>
        {title}
      </h2>
      {subtitle && <p className="text-sm sm:text-base text-white/50">{subtitle}</p>}
    </div>
  );
}
