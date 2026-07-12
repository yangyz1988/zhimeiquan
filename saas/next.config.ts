import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // standalone 输出在 Docker/Linux 构建时启用
  // Windows 开发环境需要关闭（symlink 限制）
  output: process.platform === "win32" ? undefined : "standalone",

  // 生产环境安全头
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
        ],
      },
    ];
  },

  // 图片域名白名单（Clerk + 常见 CDN）
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "img.clerk.com" },
      { protocol: "https", hostname: "images.clerk.dev" },
      { protocol: "https", hostname: "*.siliconflow.cn" },
    ],
  },

  // 禁止 /api/ 以外的路径被外部直接代理
  poweredByHeader: false,
};

export default nextConfig;
