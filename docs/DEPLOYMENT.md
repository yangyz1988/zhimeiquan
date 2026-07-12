# 智媒圈 部署指南

> 版本: 0.7.0 | 更新日期: 2026-06-29

---

## 方案一：Docker Compose 一键部署（推荐）

适用：自托管 / VPS / 内网部署 / 私有云

### 前置准备

```bash
# 1. 确保服务器安装 Docker >= 24 和 Docker Compose >= 2.20
docker --version
docker compose version

# 2. 克隆项目
git clone <repo-url> 智媒圈
cd 智媒圈

# 3. 创建数据持久化目录
mkdir -p data output

# 4. 配置环境变量
cp .env.production.example .env
# 编辑 .env，至少填入 DEEPSEEK_API_KEY
```

### 一键启动

```bash
# 启动生产环境（6 个服务：saas, api, postgres, redis, nginx, prisma-migrate）
docker compose -f docker-compose.prod.yml up -d

# 等待服务就绪（约 30-60 秒）
sleep 30

# 验证所有服务健康
docker compose -f docker-compose.prod.yml ps

# 验证 API 健康
curl http://localhost:8000/health

# 验证 Nginx 入口
curl http://localhost/
```

### 服务端口一览

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80, 443 | 反向代理 + SSL |
| API (FastAPI) | 8000 | 后端 API + Swagger 文档 |
| SaaS (Next.js) | 3000 | 前端应用 |
| PostgreSQL | 5432 | 生产数据库（仅内部） |
| Redis | 6379 | 缓存/限流（仅内部） |

### 停止和清理

```bash
# 停止所有服务
docker compose -f docker-compose.prod.yml down

# 停止并删除数据卷（⚠️ 会删除所有数据）
docker compose -f docker-compose.prod.yml down -v
```

---

## 方案二：Vercel + Railway（推荐 SaaS）

适用：海外用户 / 不想运维服务器 / 快速上线

### 2.1 前端 → Vercel

```bash
# 1. 安装 Vercel CLI
npm i -g vercel

# 2. 登录并部署
cd saas
vercel login
vercel --prod

# 3. 在 Vercel Dashboard 设置环境变量:
#    - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
#    - CLERK_SECRET_KEY
#    - DATABASE_URL (指向 Railway PostgreSQL)
#    - NEXT_PUBLIC_APP_URL (Vercel 域名)
#    - API_URL (指向 Railway API 域名)
#    - DEEPSEEK_API_KEY
#    - API_SECRET
```

**注意:** Vercel 是 Serverless 部署，LLM 调用超时建议设置为 120s。

### 2.2 后端 → Railway

```bash
# 1. 安装 Railway CLI
npm i -g @railway/cli
railway login

# 2. 初始化并部署
cd ../scripts
railway init
railway up -d

# 3. 添加 Railway 内置服务
railway service add postgres   # 自动配置 DATABASE_URL
railway service add redis      # 自动配置 REDIS_URL

# 4. 设置环境变量
railway variables set DEEPSEEK_API_KEY=sk-your-key
railway variables set API_SECRET=$(openssl rand -hex 32)
railway variables set FRONTEND_URL=https://your-app.vercel.app

# 5. 设置启动命令
railway variables set STARTUP_COMMAND="uvicorn main:app --host 0.0.0.0 --port $PORT"
```

### 2.3 数据库迁移

```bash
# 在 Railway 控制台执行
cd saas
npx prisma migrate deploy
```

### 2.4 优势对比

| 特性 | Vercel + Railway | Docker Compose |
|------|------------------|----------------|
| 部署复杂度 | 极低（零配置） | 中等 |
| 费用 | 按用量付费 | 服务器固定费用 |
| 自动 HTTPS | ✅ | 需手动配置 |
| 自动扩缩容 | ✅ | 需手动 |
| 数据持久化 | 需外部 PG | 内置 |
| 适合场景 | 海外用户、快速上线 | 国内合规、完全控制 |

---

## 方案三：GitHub Actions 自动部署

CI/CD 流水线已配置在 `.github/workflows/` 目录下。

### 3.1 配置 GitHub Secrets

在仓库 Settings → Secrets and variables → Actions 中添加：

| Secret | 说明 |
|--------|------|
| `VERCEL_TOKEN` | Vercel API Token |
| `VERCEL_ORG_ID` | Vercel Organization ID |
| `VERCEL_PROJECT_ID` | Vercel Project ID |
| `RAILWAY_TOKEN` | Railway API Token |
| `DEEPSEEK_API_KEY` | LLM API 密钥 |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk 公钥 |
| `CLERK_SECRET_KEY` | Clerk 私钥 |
| `DATABASE_URL` | 生产数据库连接串 |

### 3.2 部署流程

```
push to main
    │
    ▼
1. 安装依赖 (pnpm install + pip install)
    │
    ▼
2. 运行测试 (pytest + vitest)
    │
    ▼
3. 类型检查 (tsc)
    │
    ▼
4. 构建 (next build)
    │
    ▼
5. 部署到 Vercel / Railway
```

---

## 方案四：云平台详细部署

### 4.1 AWS EC2 部署

```bash
# 1. 创建 EC2 实例 (Ubuntu 22.04)
aws ec2 run-instances --instance-type t3.medium --security-group-ids sg-xxx

# 2. SSH 连接
ssh -i ~/.ssh/your-key.pem ubuntu@<public-ip>

# 3. 安装 Docker
sudo apt update && sudo apt install -y docker.io docker-compose-plugin

# 4. 克隆项目并部署
git clone <repo-url> 智媒圈
cd 智媒圈

# 5. 配置安全组
# 打开 80, 443, 22 端口

# 6. 启动
cp .env.production.example .env
# 编辑 .env
docker compose -f docker-compose.prod.yml up -d
```

### 4.2 阿里云 ECS 部署

```bash
# 1. 创建 ECS 实例 (CentOS 7+/Ubuntu 20.04+)
# 2. 安全组开放 80, 443, 22 端口
# 3. SSH 连接后安装 Docker
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun

# 4. 配置 Docker 镜像加速器（阿里云）
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": ["https://your-id.mirror.aliyuncs.com"]
}
EOF
sudo systemctl daemon-reload && sudo systemctl restart docker

# 5. 部署项目
git clone <repo-url> 智媒圈
cd 智媒圈
docker compose -f docker-compose.prod.yml up -d
```

---

## SSL/HTTPS 配置

### 使用 Let's Encrypt 免费证书

```bash
# 1. 安装 Certbot
sudo apt update && sudo apt install -y certbot python3-certbot-nginx

# 2. 申请证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 3. 自动续期（certbot 通常会自动配置 cron）
sudo certbot renew --dry-run

# 4. 更新 Nginx 配置以使用 HTTPS
# deploy/nginx/default.conf 中添加:
# listen 443 ssl;
# ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
```

### Docker 内 SSL 配置

```bash
# 1. 将证书放到 deploy/nginx/ssl/
mkdir -p deploy/nginx/ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem deploy/nginx/ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem deploy/nginx/ssl/

# 2. 更新 nginx 配置
# deploy/nginx/default.conf 添加 SSL 块
```

---

## DNS 配置

| 记录类型 | 名称 | 值 | 说明 |
|----------|------|-----|------|
| A | @ | <服务器IP> | 主域名 |
| A | www | <服务器IP> | WWW 子域名 |
| CNAME | api | api.your-domain.com | API 域名（如分开部署） |

---

## 性能调优

### API 后端

```bash
# Uvicorn workers 数量 = CPU 核数 × 2 + 1
# 在 docker-compose.prod.yml 中:
# environment:
#   - UVICORN_WORKERS=8

# Redis 内存限制（防止 OOM）
# redis:
#   command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

# PostgreSQL 连接池
# 在 prisma schema 中设置:
# DATABASE_URL="postgresql://...?connection_limit=10&pool_timeout=30"
```

### Nginx 调优

```nginx
# deploy/nginx/default.conf 添加:
worker_processes auto;
worker_rlimit_nofile 65535;

location /api/v1/ {
    proxy_pass http://api:8000;
    proxy_read_timeout 300s;      # SSE 长连接
    proxy_send_timeout 300s;
    proxy_buffering off;          # SSE 需要关闭缓冲
    proxy_cache off;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
}
```

### 前端 Next.js

```bash
# 启用 Turbopack（开发环境更快）
pnpm dev --turbopack

# 生产环境启用 ISR
# 在 page.tsx 中:
export const revalidate = 3600  # 每小时重新验证
```

---

## 监控与日志

### 健康检查

```bash
# API 健康
curl http://localhost:8000/health
curl http://localhost:8000/ready

# Prometheus 指标
curl http://localhost:8000/metrics

# Nginx 入口
curl http://localhost/
```

### 日志查看

```bash
# 所有服务日志
docker compose -f docker-compose.prod.yml logs -f

# 按服务查看
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f saas

# 最近 100 行
docker compose -f docker-compose.prod.yml logs --tail=100 api
```

### 推荐监控栈

| 工具 | 用途 | 部署方式 |
|------|------|----------|
| Prometheus + Grafana | 指标监控 | docker-compose 追加服务 |
| Sentry | 错误追踪 | 前端/后端 SDK |
| ELK / Loki | 日志聚合 | 独立部署 |
| UptimeRobot |  uptime 监控 | 外部 SaaS |

---

## 故障排查

### API 启动失败

```bash
# 1. 查看日志
docker compose -f docker-compose.prod.yml logs api --tail=50

# 2. 检查环境变量
docker compose -f docker-compose.prod.yml config

# 3. 验证 LLM API 密钥
docker compose -f docker-compose.prod.yml exec api python -c "
from services.deepseek import DeepSeekClient
import asyncio
c = DeepSeekClient()
r = asyncio.run(c.chat('test'))
print(r)
"
```

### 前端启动失败

```bash
# 1. 检查 Prisma 迁移
docker compose -f docker-compose.prod.yml exec saas npx prisma migrate status

# 2. 手动执行迁移
docker compose -f docker-compose.prod.yml run --rm prisma-migrate

# 3. 查看前端日志
docker compose -f docker-compose.prod.yml logs saas --tail=50
```

### 数据库连接问题

```bash
# 1. 检查 PostgreSQL 状态
docker compose -f docker-compose.prod.yml logs postgres

# 2. 连接数据库
docker compose -f docker-compose.prod.yml exec postgres psql -U zhimeiquan -d zhimeiquan

# 3. 查看表结构
\dt

# 4. 检查连接数
SELECT count(*) FROM pg_stat_activity;
```

### Redis 连接问题

```bash
# 1. 检查 Redis 状态
docker compose -f docker-compose.prod.yml logs redis

# 2. 连接测试
docker compose -f docker-compose.prod.yml exec redis redis-cli ping

# 3. 内存使用
docker compose -f docker-compose.prod.yml exec redis redis-cli INFO memory
```

---

## 数据备份

### 自动备份脚本

```bash
#!/bin/bash
# deploy/scripts/backup.sh
BACKUP_DIR="/backups/zhimeiquan/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# PostgreSQL 备份
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U zhimeiquan zhimeiquan > $BACKUP_DIR/db.sql

# 数据目录备份
docker compose -f docker-compose.prod.yml cp api:/app/data $BACKUP_DIR/data
docker compose -f docker-compose.prod.yml cp saas:/app/data $BACKUP_DIR/saas-data

# 保留 30 天
find /backups/zhimeiquan/ -type d -mtime +30 -exec rm -rf {} \;

echo "备份完成: $BACKUP_DIR"
```

### 定时备份

```bash
# 加入 crontab (每天凌晨 3 点)
crontab -e
# 添加: 0 3 * * * /path/to/deploy/scripts/backup.sh
```

---

## 回滚

### Docker 回滚

```bash
# 1. 停止当前服务
docker compose -f docker-compose.prod.yml down

# 2. 切换到上一个版本
git checkout <previous-commit>

# 3. 重新启动
docker compose -f docker-compose.prod.yml up -d

# 4. 验证
curl http://localhost:8000/health
```

### Vercel 回滚

```bash
# 查看部署历史
vercel ls

# 回滚到上一个部署
vercel rollback
```

### 数据库回滚

```bash
# Prisma 回滚最近一次迁移
docker compose -f docker-compose.prod.yml exec api \
  npx prisma migrate resolve --rolled-back <migration-name>

# 从备份恢复
docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U zhimeiquan zhimeiquan < backups/latest/db.sql
```
