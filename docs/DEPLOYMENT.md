# 智媒圈 部署指南

## 方案一：Docker Compose 一键部署（推荐）

适用：自托管 / VPS / 内网部署

```bash
# 1. 准备
cp .env.production.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY / Clerk / Stripe 密钥

# 2. 一键启动
docker compose -f docker-compose.prod.yml up -d

# 3. 验证
curl http://localhost/health        # SaaS
curl http://localhost:8000/health   # API
```

启动 5 个服务：
- `saas` - Next.js 前端 (3000)
- `api` - FastAPI 后端 (8000)
- `postgres` - PostgreSQL 16
- `redis` - Redis 7 缓存
- `nginx` - 反向代理 (80/443)

## 方案二：Vercel + Railway（推荐 SaaS）

适用：海外用户 / 不想运维服务器

### 2.1 前端 → Vercel

```bash
cd saas
vercel --prod
```

需要环境变量：
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`
- `DATABASE_URL` (Railway Postgres)
- `NEXT_PUBLIC_APP_URL` (Vercel 域名)
- `API_URL` (Railway API 域名)

### 2.2 后端 → Railway

```bash
# 安装 Railway CLI
npm i -g @railway/cli
railway login
railway init
railway up
```

在 Railway Dashboard 添加：
- Redis 服务
- PostgreSQL 服务
- 设置 `DEEPSEEK_API_KEY` 等环境变量
- 设置启动命令：`uvicorn main:app --host 0.0.0.0 --port $PORT`

### 2.3 数据库迁移

```bash
# 在 Vercel/Railway 控制台执行
cd saas
npx prisma db push
```

## 方案三：GitHub Actions 自动部署

已配置 `.github/workflows/deploy.yml`：

- 推送到 `main` 分支 → 跑测试
- 测试通过 → 部署 SaaS 到 Vercel
- 测试通过 → 部署 API 到 Railway

需要在 GitHub 仓库设置 Secrets：
- `VERCEL_TOKEN` / `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID`
- `RAILWAY_TOKEN`
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` / `CLERK_SECRET_KEY`
- `DATABASE_URL`

## 环境变量清单

### 必填
| 变量 | 说明 |
|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek LLM |
| `DATABASE_URL` | PostgreSQL 或 SQLite |
| `REDIS_URL` | Redis 缓存 |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk 公钥 |
| `CLERK_SECRET_KEY` | Clerk 私钥 |

### 选填
| 变量 | 说明 |
|---|---|
| `QWEN_API_KEY` | 阿里通义 |
| `ERNIE_API_KEY` + `ERNIE_SECRET_KEY` | 百度文心 |
| `HUNYUAN_API_KEY` | 腾讯混元 |
| `OPENAI_API_KEY` | DALL-E |
| `STABILITY_API_KEY` | Stable Diffusion |
| `SILICONFLOW_API_KEY` | 硅基流动 |
| `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` | Stripe 支付 |
| `LOG_FORMAT` | `json` / `text`，生产用 `json` |
| `LOG_LEVEL` | `info` / `debug` / `warning` |

## 性能调优

### API
- workers = CPU 核数 × 2
- 启用 Redis 缓存
- 限流: 30 req/min/user

### SaaS
- 启用 Vercel Edge Cache
- 静态资源走 CDN
- 图片用 Next/Image 自动优化

## 监控

### 健康检查
- SaaS: `GET /api/health` (Next.js)
- API: `GET /health` / `GET /ready` (FastAPI)

### 日志
- JSON 格式输出到 stdout
- 推荐: Grafana / SigNoz / Datadog

### 推荐监控栈
- **应用**: Sentry
- **基础设施**: Prometheus + Grafana
- **日志**: Loki
- **APM**: SigNoz

## 故障排查

### API 启动失败
1. 检查 `DEEPSEEK_API_KEY` 是否设置
2. 检查 Redis 是否可达
3. 查看 `docker compose logs api`

### SaaS 启动失败
1. 检查 Clerk 密钥是否有效
2. 检查 `DATABASE_URL` 是否可达
3. 运行 `npx prisma db push` 同步数据库

### 性能问题
1. 检查 Redis 缓存命中率（`GET /api/v1/router/stats`）
2. 检查 LLM 调用延迟
3. 增加 uvicorn workers

## 回滚

```bash
# Docker
docker compose down
git checkout <prev-commit>
docker compose up -d

# Vercel
vercel rollback
```
