# 生产部署指南

## 方案：Vercel (前端) + Railway (后端)

---

## 1. 推送到 GitHub

```bash
# 在 GitHub 创建仓库: zhimeiquan
cd D:\opencode\zhimeiquan
git remote add origin https://github.com/yourname/zhimeiquan.git
git branch -M main
git push -u origin main
```

---

## 2. Railway 部署 Python API

### 2.1 创建项目
1. 访问 https://railway.app
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 选择 `zhimeiquan` 仓库
4. 选择 `scripts` 作为根目录

### 2.2 配置环境变量
在 Railway 项目设置中添加：

```
DEEPSEEK_API_KEY=sk-your-key
REDIS_URL=redis://default:xxx@redis.railway.internal:6379
```

### 2.3 添加 Redis
1. 在 Railway 项目中点击 "New" → "Database" → "Redis"
2. 复制 Redis 连接 URL 到环境变量

### 2.4 获取 API URL
部署成功后，Railway 会分配一个 URL，例如：
`https://zhimeiquan-api.up.railway.app`

---

## 3. Vercel 部署 Next.js

### 3.1 创建项目
1. 访问 https://vercel.com
2. 点击 "New Project" → "Import Git Repository"
3. 选择 `zhimeiquan` 仓库
4. Root Directory 设置为 `saas`

### 3.2 配置环境变量
在 Vercel 项目设置中添加：

```
# AI API
DEEPSEEK_API_KEY=sk-your-key
API_URL=https://zhimeiquan-api.up.railway.app

# Clerk Auth
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx

# Database (使用 SQLite 文件存储)
DATABASE_URL=file:./prod.db
```

### 3.3 部署
点击 "Deploy"，等待构建完成。

---

## 4. 配置 Clerk

### 4.1 创建应用
1. 访问 https://clerk.com
2. 创建新应用
3. 复制 Publishable Key 和 Secret Key

### 4.2 配置回调 URL
在 Clerk Dashboard → Paths 中添加：
- `https://your-app.vercel.app/*`

---

## 5. 自定义域名 (可选)

### Vercel
1. 在 Vercel 项目 → Settings → Domains
2. 添加你的域名
3. 配置 DNS 指向 Vercel

### Railway
1. 在 Railway 项目 → Settings → Networking
2. 添加自定义域名
3. 配置 DNS 指向 Railway

---

## 6. 验证部署

```bash
# 测试前端
curl https://your-app.vercel.app

# 测试后端
curl https://your-api.up.railway.app/health
```

---

## 费用估算

| 服务 | 免费额度 | 付费起步 |
|:-----|:---------|:---------|
| Vercel | 100GB 带宽/月 | $20/月 |
| Railway | $5 额度/月 | $5/月 |
| Clerk | 10,000 MAU | $25/月 |
| DeepSeek | - | 按量付费 |

**总成本：约 $5-30/月** (取决于使用量)
