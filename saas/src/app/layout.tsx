import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ClerkProvider } from "@/components/providers";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import { ErrorBoundary } from "@/components/error-boundary";
import { Toaster } from "@/components/toaster";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    default: "智媒圈 - AI内容策略引擎 | 让每个人都能用AI做出爆款内容",
    template: "%s | 智媒圈",
  },
  description: "基于九层知识体系 + 50+专家智能体，输入关键词30秒生成可发布的赚钱内容。覆盖13个主流平台，爆款概率提升至95%+。",
  keywords: ["AI内容策略引擎", "自媒体", "爆款内容", "赚钱", "自媒体变现", "AI生成", "数据分析", "爆款监控", "DeepSeek", "智媒圈"],
  authors: [{ name: "智媒圈" }],
  creator: "智媒圈",
  openGraph: {
    type: "website",
    locale: "zh_CN",
    url: "https://zhimeiquan.ai",
    siteName: "智媒圈",
    title: "智媒圈 - AI内容策略引擎",
    description: "基于九层知识体系 + 50+专家智能体，30秒生成可发布的赚钱内容",
  },
  twitter: {
    card: "summary_large_image",
    title: "智媒圈 - AI内容策略引擎",
    description: "基于九层知识体系 + 50+专家智能体，30秒生成可发布的赚钱内容",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f97316",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="zh-CN">
        <body className={inter.className}>
          <ErrorBoundary>
            <Header />
            <main>{children}</main>
            <Footer />
            <Toaster />
          </ErrorBoundary>
        </body>
      </html>
    </ClerkProvider>
  );
}
