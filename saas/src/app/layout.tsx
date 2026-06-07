import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ClerkProvider } from "@/components/providers";
import { Header } from "@/components/header";
import { ErrorBoundary } from "@/components/error-boundary";
import { Toaster } from "@/components/toaster";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    default: "智媒圈 - AI自媒体内容工厂",
    template: "%s | 智媒圈",
  },
  description: "输入主题，30秒拿走成品。13平台覆盖，数据驱动的AI内容工厂。",
  keywords: ["AI内容生成", "自媒体", "爆款", "DeepSeek", "智媒圈"],
  authors: [{ name: "智媒圈" }],
  creator: "智媒圈",
  openGraph: {
    type: "website",
    locale: "zh_CN",
    url: "https://zhimeiquan.ai",
    siteName: "智媒圈",
    title: "智媒圈 - AI自媒体内容工厂",
    description: "输入主题，30秒拿走成品。13平台覆盖，数据驱动。",
  },
  twitter: {
    card: "summary_large_image",
    title: "智媒圈 - AI自媒体内容工厂",
    description: "输入主题，30秒拿走成品",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
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
            <Toaster />
          </ErrorBoundary>
        </body>
      </html>
    </ClerkProvider>
  );
}
