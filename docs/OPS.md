# 智媒圈 运维手册

> 版本: 0.7.0 | 更新日期: 2026-06-27

---

## 目录

1. [快速启动](#1-快速启动)
2. [环境变量说明](#2-环境变量说明)
3. [数据目录结构](#3-数据目录结构)
4. [数据备份策略](#4-数据备份策略)
5. [监控告警](#5-监控告警)
6. [日志说明](#6-日志说明)
7. [密钥管理](#7-密钥管理)
8. [常见问题排查](#8-常见问题排查)
9. [安全最佳实践](#9-安全最佳实践)
10. [部署指南](#10-部署指南)
11. [升级指南](#11-升级指南)
12. [回滚指南](#12-回滚指南)
13. [监控指南](#13-监控指南)
14. [故障排查](#14-故障排查)
15. [安全指南](#15-安全指南)

---

## 1. 快速启动

### 方式一：Docker Compose（推荐开发环境）

```bash
# 1. 克隆项目
git clone <repo-url> 智媒圈
cd 智媒圈

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，至少填入 DEEPSEEK_API_KEY

# 3. 一键启动（开发环境，4 个服务）
docker compose up -d

# 4. 查看状态
docker compose ps
docker compose logs -f

# 5. 访问
# 前端: http://localhost:3000
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

开发环境启动的服务:
| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| saas | Next.js (自建) | 3000 | 前端应用 |
| api | FastAPI (自建) | 8000 | 后端 API |
| redis | redis:7-alpine | 6379 | 缓存/限流 |
| nginx | nginx:alpine | 80, 443 | 反向代理 |

### 方式二：本地开发（不依赖 Docker）

**后端:**
```bash
cd scripts

# 创建虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example ../.env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**前端:**
```bash
cd saas

# 安装依赖
pnpm install

# Prisma 数据库初始化
pnpm db:generate
pnpm db:push

# 配置环境变量
cp .env.example .env.local
# 编辑 .env.local，填入 Clerk 密钥

# 启动开发服务器
pnpm dev
```

### 方式三：生产部署

```bash
# 1. 配置生产环境变量
cp .env.production.example .env
# 编辑 .env，填入所有必填密钥

# 2. 启动（Prisma 迁移自动执行）
docker compose -f docker-compose.prod.yml up -d

# 3. 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 4. 手动执行数据库迁移（如需）
docker compose -f docker-compose.prod.yml run --rm prisma-migrate

# 5. 健康检查
curl http://localhost:8000/health
curl http://localhost:80/  # 通过 Nginx
```

生产环境启动的服务:
| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| saas | Next.js (自建) | 3000 | 前端应用 |
| api | FastAPI (自建) | 8000 | 后端 API |
| postgres | postgres:16-alpine | 5432 | 生产数据库 |
| redis | redis:7-alpine | 6379 | 缓存/限流 |
| nginx | nginx:alpine | 80, 443 | 反向代理+SSL |
| prisma-migrate | Next.js (一次性) | - | 数据库迁移 |

### 启动脚本

项目根目录提供 PowerShell 启动脚本:

```powershell
# 开发环境启动
.\dev-start.ps1

# 生产环境启动
.\start.ps1
```

---

## 2. 环境变量说明

### 必填变量

| 变量 | 说明 | 默认值 | 开发 | 生产 |
|------|------|--------|:----:|:----:|
| `DEEPSEEK_API_KEY` | DeepSeek LLM API 密钥 | - | 必填 | 必填 |
| `DATABASE_URL` | 数据库连接串 | `file:./dev.db` | 可选 | 必填 |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk 公钥 | - | 必填 | 必填 |
| `CLERK_SECRET_KEY` | Clerk 密钥 | - | 必填 | 必填 |

### LLM 模型变量

| 变量 | 说明 | 默认值 | 必填 |
|------|------|--------|:----:|
| `QWEN_API_KEY` | 通义千问 API 密钥 | - | 否 |
| `ERNIE_API_KEY` | 文心一言 API 密钥 | - | 否 |
| `ERNIE_SECRET_KEY` | 文心一言 Secret | - | 否 |
| `HUNYUAN_API_KEY` | 混元 API 密钥 | - | 否 |
| `OPENAI_API_KEY` | OpenAI API 密钥 (DALL-E) | - | 否 |
| `STABILITY_API_KEY` | Stability AI API 密钥 | - | 否 |
| `SILICONFLOW_API_KEY` | SiliconFlow 密钥 (视频/图像) | - | 否 |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com` | 否 |

### 支付变量

| 变量 | 说明 | 默认值 | 必填 |
|------|------|--------|:----:|
| `STRIPE_SECRET_KEY` | Stripe 密钥 | - | 否 (无支付则不用) |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook 密钥 | - | 否 |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe 公钥 | - | 否 |

### 基础架构变量

| 变量 | 说明 | 默认值 | 必填 |
|------|------|--------|:----:|
| `REDIS_URL` | Redis 连接串 | `redis://localhost:6379` | 否 |
| `API_SECRET` | 前后端共享密钥 | - | 推荐 |
| `FRONTEND_URL` | 前端 URL | `https://www.zhimeiquan.com` | 否 |
| `NEXT_PUBLIC_APP_URL` | 前端公开 URL | - | 否 (生产推荐) |
| `POSTGRES_USER` | PostgreSQL 用户名 | `zhimeiquan` | 否 (生产) |
| `POSTGRES_PASSWORD` | PostgreSQL 密码 | - | 是 (生产) |
| `POSTGRES_DB` | PostgreSQL 数据库名 | `zhimeiquan` | 否 (生产) |

### 日志变量

| 变量 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| `LOG_FORMAT` | 日志格式 | `json` | `json` / `text` |
| `LOG_LEVEL` | 日志级别 | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

### 内容目录变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ZHIMEIQUAN_CONTENT_DIR` | 知识库路径 | `../content` |

### 环境变量配置文件位置

- **开发环境**: 项目根目录 `.env`（或前端 `.env.local`）
- **生产环境**: 项目根目录 `.env`（使用 `docker-compose.prod.yml`）
- **环境变量模板**: `.env.example`（开发）、`.env.production.example`（生产）

---

## 3. 数据目录结构

```
智媒圈/
├── data/                          # 运行时数据根目录
│   ├── rules/                     # 13 个平台爆款规则 JSON
│   │   ├── 抖音.json
│   │   ├── 小红书.json
│   │   ├── B站.json
│   │   ├── 微博.json
│   │   ├── 知乎.json
│   │   ├── 头条.json
│   │   ├── 快手.json
│   │   ├── YouTube.json
│   │   ├── TikTok.json
│   │   ├── 公众号.json
│   │   ├── 视频号.json
│   │   ├── 百度热搜.json
│   │   └── Instagram.json
│   ├── analytics/                 # 内容表现数据 (JSON)
│   │   └── {project_id}_{content_id}.json
│   ├── ab_tests/                  # A/B 测试数据
│   │   └── {test_id}.json
│   ├── agents/                    # Agent 数据
│   │   ├── queue.json             # 自动发布任务队列
│   │   ├── activity.log           # Agent 活动日志
│   │   └── matrix/                # 矩阵发布任务
│   ├── scheduled/                 # 调度队列
│   │   └── queue.json
│   ├── teams/                     # 团队数据
│   │   ├── teams.json             # 团队列表
│   │   ├── invitations.json       # 邀请记录
│   │   └── shares.json            # 分享记录
│   ├── templates/                 # 内容模板
│   │   ├── tutorial_basic.json
│   │   ├── review_product.json
│   │   ├── opinion_hot.json
│   │   └── vlog_daily.json
│   ├── competitors/               # 竞品监控数据
│   │   ├── _competitors.json      # 竞品索引
│   │   └── {competitor_id}/       # 单个竞品内容记录
│   ├── videos/                    # 生成的视频/音频/封面
│   ├── images/                    # 生成的图片
│   ├── insights/                  # 洞察报告缓存
│   │   └── {user_id}_{type}.json
│   ├── rewrites/                  # 改写记录
│   │   └── rewrite_{content_id}.json
│   ├── workflows/                 # 自动化工作流定义
│   │   └── wf_{timestamp}.json
│   └── router_history/            # 模型路由历史 (JSONL)
│       └── calls_{date}.jsonl
├── output/                        # 校准数据库位置
│   └── tracker.db                 # Fire Score 校准 (SQLite)
└── content/                       # 知识库 (Git 管理)
    ├── methodology/               # 10 套方法论文档
    ├── templates/                 # 13 个平台模板文件
    ├── experts/                   # 50+ 专家人设
    └── prompts/                   # 提示词工程
```

### 存储说明

| 目录 | 存储类型 | 是否需要备份 | 说明 |
|------|----------|:-----------:|------|
| `data/rules/` | JSON | 否 | 自动生成，可重新采集 |
| `data/analytics/` | JSON | 是 | 用户内容表现数据 |
| `data/ab_tests/` | JSON | 是 | A/B 测试数据 |
| `data/agents/` | JSON | 是 | Agent 任务配置 |
| data/scheduled/ | JSON | 是 | 发布调度队列 |
| data/teams/ | JSON | 是 | 团队和邀请数据 |
| data/templates/ | JSON | 可选 | 模板，可重新创建 |
| data/competitors/ | JSON | 是 | 竞品监控数据 |
| data/insights/ | JSON | 可选 | 洞察缓存，可重新生成 |
| data/rewrites/ | JSON | 可选 | 改写记录日志 |
| data/workflows/ | JSON | 是 | 自动化工作流配置 |
| data/router_history/ | JSONL | 可选 | 路由历史，用于学习优化 |
| data/videos/ | 媒体文件 | 可选 | 生成的可再生文件 |
| data/images/ | 媒体文件 | 可选 | 生成的可再生文件 |
| output/tracker.db | SQLite | 是 | Fire Score 校准数据 |
| content/ | Markdown | 是 (Git) | 知识库由 Git 管理 |

---

## 4. 数据备份策略

### 需要定期备份的数据

| 数据 | 备份方式 | 推荐频率 | 保留策略 |
|------|----------|----------|----------|
| PostgreSQL 数据库 | `pg_dump` | 每日 | 保留 30 天 |
| SQLite (output/tracker.db) | 复制文件 | 每日 | 保留 30 天 |
| data/analytics/ | 压缩归档 | 每日 | 保留 30 天 |
| data/teams/ | 压缩归档 | 每日 | 保留 30 天 |
| data/workflows/ | 压缩归档 | 每日 | 保留 30 天 |
| 知识库 content/ | Git 仓库 | 每次变更 | 永久 |

### 备份脚本示例

```bash
#!/bin/bash
# 数据库备份
BACKUP_DIR="/backups/zhimeiquan/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# PostgreSQL 备份（生产环境）
docker exec zhimeiquan_postgres_1 pg_dump -U zhimeiquan zhimeiquan > $BACKUP_DIR/db.sql

# SQLite 备份
cp /path/to/output/tracker.db $BACKUP_DIR/tracker.db

# 数据目录备份
tar -czf $BACKUP_DIR/data.tar.gz \
  /path/to/data/analytics/ \
  /path/to/data/teams/ \
  /path/to/data/workflows/ \
  /path/to/data/competitors/

# 清理 30 天前的备份
find /backups/zhimeiquan/ -type d -mtime +30 -exec rm -rf {} \;
```

### Docker Volume 备份

```bash
# 备份 Docker volumes
docker run --rm -v zhimeiquan_postgres_data:/source -v /backups:/backup alpine \
  tar -czf /backup/postgres_$(date +%Y%m%d).tar.gz -C /source .

docker run --rm -v zhimeiquan_redis_data:/source -v /backups:/backup alpine \
  tar -czf /backup/redis_$(date +%Y%m%d).tar.gz -C /source .
```

### 恢复步骤

```bash
# PostgreSQL 恢复
docker exec -i zhimeiquan_postgres_1 psql -U zhimeiquan zhimeiquan < backup.sql

# SQLite 恢复
cp tracker.db.backup /path/to/output/tracker.db

# 数据目录恢复
tar -xzf data.tar.gz -C /path/to/
```

---

## 5. 监控告警

### 健康检查端点

| 端点 | 用途 | 检查内容 | 建议检查间隔 |
|------|------|----------|:-----------:|
| `/health` | Liveness | 服务是否运行 | 30 秒 |
| `/ready` | Readiness | 依赖是否就绪(Redis, DeepSeek) | 30 秒 |
| `/metrics` | Prometheus | 请求数、错误率、缓存命中率 | 15 秒 |

### Docker 健康检查

所有服务均配置了健康检查（在 `docker-compose.yml` 中）：

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8000/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Prometheus 指标

端点 `/metrics` 返回 Prometheus 文本格式:

```
# HELP zhimeiquan_requests_total 总请求数
# TYPE zhimeiquan_requests_total counter
zhimeiquan_requests_total 15234

# HELP zhimeiquan_request_errors_total 请求错误数
# TYPE zhimeiquan_request_errors_total counter
zhimeiquan_request_errors_total 23

# HELP zhimeiquan_request_duration_ms 请求耗时（毫秒）
# TYPE zhimeiquan_request_duration_ms summary
zhimeiquan_request_duration_ms{quantile="avg"} 245.8
zhimeiquan_request_duration_ms{quantile="p99"} 1890.5

# HELP zhimeiquan_cache_hit_rate 缓存命中率
# TYPE zhimeiquan_cache_hit_rate gauge
zhimeiquan_cache_hit_rate 0.85

# HELP zhimeiquan_llm_calls_total LLM 调用总数
# TYPE zhimeiquan_llm_calls_total counter
zhimeiquan_llm_calls_total{model="deepseek"} 1234
zhimeiquan_llm_calls_total{model="qwen"} 456
```

### 关键监控指标

| 指标 | 告警阈值 | 说明 |
|------|----------|------|
| 请求错误率 | > 5% | HTTP 4xx/5xx 比例 |
| P99 延迟 | > 3000ms | 请求耗时过高 |
| 缓存命中率 | < 50% | 缓存效率低需检查 |
| LLM 成功率 | < 95% | 模型调用失败过多 |
| 活跃用户 | 突降 50%+ | 可能存在问题 |

### 推荐告警规则 (Prometheus)

```yaml
groups:
  - name: zhimeiquan
    rules:
      - alert: HighErrorRate
        expr: rate(zhimeiquan_request_errors_total[5m]) / rate(zhimeiquan_requests_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "错误率超过 5%"

      - alert: HighLatency
        expr: zhimeiquan_request_duration_ms{quantile="p99"} > 3000
        for: 5m
        annotations:
          summary: "P99 延迟超过 3 秒"

      - alert: LLMFailures
        expr: rate(zhimeiquan_llm_failures_total[5m]) > 0
        for: 2m
        annotations:
          summary: "LLM 调用失败"

      - alert: LowCacheHitRate
        expr: zhimeiquan_cache_hit_rate < 0.5
        for: 10m
        annotations:
          summary: "缓存命中率低于 50%"
```

---

## 6. 日志说明

### 日志格式

默认使用 JSON 格式（由 `LOG_FORMAT=json` 控制）:

```json
{
  "timestamp": "2026-06-26 10:00:00,123",
  "level": "INFO",
  "logger": "zhimeiquan",
  "message": "内容生成成功",
  "topic": "AI 工具推荐",
  "platform": "抖音",
  "model": "deepseek"
}
```

设置 `LOG_FORMAT=text` 可使用文本格式:

```
2026-06-26 10:00:00,123 [INFO] zhimeiquan: 内容生成成功
```

### 日志级别

| 级别 | 用途 | 示例场景 |
|------|------|----------|
| DEBUG | 调试信息 | LLM 原始响应、缓存操作细节 |
| INFO | 正常运行 | API 调用成功、数据记录 |
| WARNING | 可恢复问题 | Redis 不可用(降级)、缓存未命中 |
| ERROR | 需要关注 | API 调用失败、LLM 超时、异常 |

### 关键日志事件

**正常操作日志:**
```
INFO: 内容生成成功      (topic="AI工具", platform="抖音", model="deepseek")
INFO: Fire Score 评分完成 (score=85, platform="小红书")
INFO: 内容发布记录已保存  (project_id="proj_001")
INFO: 竞品账号添加成功    (account_name="竞品A")
INFO: 团队已创建          (team_id="team_abc")
INFO: 工作流已触发        (workflow_id="wf_xxx")
```

**警告日志:**
```
WARNING: Redis 不可用，降级为内存缓存
WARNING: 平台规则加载失败，使用默认规则
WARNING: 写入路由历史失败
```

**错误日志:**
```
ERROR: AI 返回格式错误       (topic="...")
ERROR: 内容生成失败           (error="...")
ERROR: SSE 流式生成失败       (error="...")
ERROR: 数字人视频生成失败
```

---

## 7. 密钥管理

### 密钥清单

| 密钥 | 获取方式 | 轮换建议 |
|------|----------|----------|
| `DEEPSEEK_API_KEY` | platform.deepseek.com | 每 90 天 |
| `QWEN_API_KEY` | dashscope.aliyun.com | 每 90 天 |
| `ERNIE_API_KEY` + `ERNIE_SECRET_KEY` | console.bce.baidu.com | 每 90 天 |
| `HUNYUAN_API_KEY` | console.cloud.tencent.com | 每 90 天 |
| `OPENAI_API_KEY` | platform.openai.com | 每 90 天 |
| `CLERK_SECRET_KEY` | dashboard.clerk.com | 每 180 天 |
| `STRIPE_SECRET_KEY` | dashboard.stripe.com | 每 180 天 |
| `API_SECRET` | 自行生成 | 每 90 天 |

### 密钥文件安全

- `.env`、`.env.local`、`.env.production` **永远不要提交到 Git**
- 生产环境推荐使用 Docker Secrets 或 K8s Secrets
- `.env.example` 仅包含占位符，可安全提交

### 最佳实践

```bash
# 生成安全的 API_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 使用 Docker Secrets（生产环境）
# docker-compose.prod.yml 中:
# secrets:
#   deepseek_key:
#     file: ./secrets/deepseek_key.txt
```

---

## 8. 常见问题排查

### API 返回 503

**症状:** 所有请求返回 `Service Unavailable`

**排查步骤:**
1. 检查 `docker compose ps` 确认 api 服务是否运行
2. 检查 `/health` 端点: `curl http://localhost:8000/health`
3. 检查日志: `docker compose logs api --tail=50`
4. 重启服务: `docker compose restart api`

### Prisma 连接失败

**症状:** 前端报数据库错误，启动容器后立即退出

**排查步骤:**
1. 确认 PostgreSQL 已就绪: `docker compose logs postgres`
2. 确认 `DATABASE_URL` 配置正确
3. 手动执行迁移: `docker compose -f docker-compose.prod.yml run --rm prisma-migrate`
4. 检查 PostgreSQL 用户权限
5. 确认数据库已创建: `docker compose exec postgres psql -U zhimeiquan -c '\l'`

**常见原因:**
- `POSTGRES_PASSWORD` 为空或包含特殊字符
- PostgreSQL 容器启动慢，迁移依赖超时
- Prisma schema 与数据库版本不兼容

### Redis 不可用

**症状:** 日志出现 `Redis 不可用，降级为内存缓存`

**影响:** 服务自动降级为内存缓存，功能和数据不受影响，但:
- 缓存容量限制为 1000 条
- 限流不精确（内存滑动窗口）
- 重启后缓存丢失

**排查步骤:**
1. `docker compose logs redis` 检查 Redis 状态
2. `docker compose exec redis redis-cli ping` 检查连通性
3. 检查 `REDIS_URL` 配置
4. `docker compose restart redis`

### LLM 调用超时

**症状:** 内容生成或评分 API 响应缓慢或超时

**排查步骤:**
1. 检查 API Key 是否有效: `curl https://api.deepseek.com/v1/models -H "Authorization: Bearer $DEEPSEEK_API_KEY"`
2. 检查网络连接（某些云环境可能无法访问 DeepSeek API）
3. 检查模型路由历史: `curl http://localhost:8000/api/v1/router/stats`
4. 检查是否被限流（429 Too Many Requests）
5. 降级测试: 将 `priority` 设为 `speed` 使用更快的模型

### 平台采集失败

**症状:** 平台规则未更新或采集日志报错

**排查步骤:**
1. 检查平台是否变更了 API 或页面结构
2. 查看日志错误信息: `docker compose logs api | grep scraper`
3. 检查目标平台是否可以正常访问（可能需要 VPN）
4. 手动触发刷新: `curl -X POST http://localhost:8000/api/v1/monitor/rules/refresh`
5. 多源降级: 平台 API 不可用时会自动尝试 RSS 和第三方 API

### Docker 启动问题

**问题: 数据库文件权限问题**
```bash
# 错误: Permission denied 或 Can't create database
# 解决方案: 创建目录并设置权限
mkdir -p data/analytics data/rules data/ab_tests data/agents data/scheduled data/teams data/templates data/competitors data/videos data/images data/insights data/rewrites data/workflows data/router_history
chmod 755 data/
```

**问题: 端口冲突**
```bash
# 检查端口占用
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Linux/Mac

# 修改端口映射（在 docker-compose.yml 中）
services:
  api:
    ports:
      - "8001:8000"  # 宿主机 8001 -> 容器 8000
```

**问题: 内存不足**
```bash
# 限制 Docker 容器内存使用
docker compose up -d --memory="512m" --memory-swap="1g"
```

---

## 9. 安全最佳实践

### CORS 配置

`main.py` 中的 CORS 配置应仅限于受信任的来源:

```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # 开发环境
    os.getenv("FRONTEND_URL", "https://www.zhimeiquan.com"),  # 生产环境
]
```

生产环境中**不要**使用 `allow_origins=["*"]`。

### API 密钥验证

- 启用 `API_SECRET` 环境变量（前后端共享密钥）
- 所有请求（除健康检查外）需要携带 `X-API-Key` 头部
- 密钥应随机生成，长度至少 32 字符

### 输入安全

系统内置多层输入保护:
- HTML 标签清洗 (`strip_html_tags`)
- XSS 防护 (`sanitize_input`)
- URL 安全验证 (`validate_url`)
- 内容长度限制 (`CONTENT_LIMITS`)
- 特殊字符过滤

### 限流保护

| 层级 | 限制 | 说明 |
|------|------|------|
| 内容生成 | 30 次/平台/分钟 | 防止 API 滥用 |
| 其他 API | 60 次/分钟 | 通用限流 |
| 未认证 | 10 次/分钟 | 匿名请求限制 |

### 网络隔离

生产环境推荐:
- 将 API 和数据库放在内网，不对外暴露数据库端口
- Nginx 反向代理作为唯一入口
- 启用 HTTPS (Let's Encrypt 免费证书)
- 配置防火墙规则，仅开放 80/443 端口

### 数据安全

- 知识库内容 (`content/`) 使用 Git 管理，做好权限控制
- 用户内容数据存储在 `data/analytics/`，按项目 ID 隔离
- SQLite 数据文件 (`output/tracker.db`) 应设置合适的文件权限
- 日志中不要记录敏感信息（API Key、密码、Token）

---

## 10. 部署指南

### 10.1 Docker Compose 部署（推荐）

适用于自有服务器部署，支持开发和生产两种模式。

#### 前置准备

```bash
# 1. 确保服务器安装了 Docker 和 Docker Compose
# Docker >= 24, Docker Compose >= 2.20

# 2. 克隆项目
git clone <repo-url> 智媒圈
cd 智媒圈

# 3. 创建数据目录
mkdir -p data output
```

#### 开发环境部署

```bash
# 配置环境变量
cp .env.example .env
cat >> .env << EOF
DEEPSEEK_API_KEY=sk-your-key-here
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk-your-key
CLERK_SECRET_KEY=sk-your-secret
EOF

# 启动
docker compose up -d

# 等待服务就绪（约 30 秒）
sleep 30
docker compose ps

# 验证
curl http://localhost:8000/health
curl http://localhost:3000
```

#### 生产环境部署

```bash
# 配置生产环境变量
cp .env.production.example .env
# 必须设置:
# - DEEPSEEK_API_KEY
# - POSTGRES_PASSWORD（强烈建议使用强密码）
# - API_SECRET（随机生成）
# - FRONTEND_URL（你的域名）
# - NEXT_PUBLIC_APP_URL（你的域名）

# 启动生产环境
docker compose -f docker-compose.prod.yml up -d

# 验证所有服务健康
for svc in saas api postgres redis nginx; do
  echo -n "$svc: "
  docker compose ps $svc | grep -q "healthy" && echo "OK" || echo "CHECKING..."
done
```

#### Nginx 配置

```nginx
# deploy/nginx/default.conf
upstream saas {
    server saas:3000;
}

upstream api {
    server api:8000;
}

# 前端代理
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://saas;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # API 代理
    location /api/ {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_read_timeout 120s;  # SSE 长连接
        proxy_buffering off;      # SSE 需要关闭缓冲
    }

    # 健康检查
    location /health {
        proxy_pass http://api;
    }
}
```

#### 启用 HTTPS (Let's Encrypt)

```bash
# 安装 Certbot
apt-get update && apt-get install -y certbot python3-certbot-nginx

# 申请证书
certbot --nginx -d your-domain.com

# 自动续期（加入 crontab）
crontab -e
# 添加: 0 3 * * * certbot renew --quiet && docker compose reload nginx
```

### 10.2 Vercel 部署

适用于前端 Next.js 快速部署。

```bash
# 1. 安装 Vercel CLI
npm i -g vercel

# 2. 登录并部署
cd saas
vercel login
vercel --prod

# 3. 环境变量配置
# 在 Vercel Dashboard → Settings → Environment Variables 中设置:
# - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
# - CLERK_SECRET_KEY
# - DEEPSEEK_API_KEY
# - DATABASE_URL (指向外部 PostgreSQL)

# 4. API 代理配置
# 在 saas/vercel.json 中配置 API 代理到后端:
# {
#   "rewrites": [
#     { "source": "/api/(.*)", "destination": "https://api.your-domain.com/$1" }
#   ]
# }
```

**注意:** Vercel 部署的后端需要单独部署（见 Railway）。

### 10.3 Railway 部署

适用于全栈一键部署。

```bash
# 1. 安装 Railway CLI
npm i -g @railway/cli

# 2. 登录
railway login

# 3. 新建项目并关联
cd scripts
railway init
railway up -d  # 部署后端服务

# 4. 设置环境变量
railway variables set DEEPSEEK_API_KEY=sk-your-key
railway variables set REDIS_URL=$RAILWAY_REDIS_URL  # Railway 自动提供 Redis

# 5. 前端同样部署
cd ../saas
railway up -d

# 6. 获取公开 URL
railway domain
```

**Railway 优势:**
- 自动提供 PostgreSQL 和 Redis 服务
- 自动 HTTPS
- 按用量计费
- 零配置 CI/CD（push to main 自动部署）

### 10.4 云平台对照表

| 平台 | 前端 | 后端 | 数据库 | 缓存 | 适合场景 |
|------|------|------|--------|------|----------|
| Docker Compose | 自建 | 自建 | 自建 | 自建 | 完全控制、私有部署 |
| Vercel | 托管 | 需要外部 API | 需要外部 PG | 需要外部 Redis | 前端快速上线 |
| Railway | 托管 | 托管 | 托管 | 托管 | 全栈一体化 |
| AWS EC2 | 自建 | 自建 | RDS | ElastiCache | 企业级生产 |
| 阿里云 ECS | 自建 | 自建 | RDS | Redis | 国内合规部署 |

---

## 11. 升级指南

### 11.1 版本兼容性

| 版本 | Python | Node.js | Docker Compose | 备注 |
|------|---------|---------|----------------|------|
| 0.7.x | 3.12+ | 22+ | >= 2.20 | 当前版本 |
| 0.6.x | 3.11+ | 20+ | >= 2.20 | 上一版本 |

### 11.2 升级前检查清单

```bash
# 1. 备份当前数据
./scripts/backup.sh  # 如有备份脚本

# 2. 查看变更日志
git log HEAD..origin/main --oneline  # 查看待升级的变更

# 3. 检查环境变量是否有新增项
diff .env .env.example  # 对比是否有遗漏的新变量

# 4. 确认当前版本
grep 'version' package.json  # 前端
grep '__version__' scripts/main.py  # 后端
```

### 11.3 滚动升级（零停机流程）

```bash
# 第一步：升级后端 API（逐个服务，先不重启 nginx）
docker compose -f docker-compose.prod.yml build api
docker compose -f docker-compose.prod.yml up -d --no-deps api

# 等待 API 就绪
sleep 15
curl -f http://localhost:8000/health || exit 1

# 第二步：升级前端 SAAS
docker compose -f docker-compose.prod.yml build saas
docker compose -f docker-compose.prod.yml up -d --no-deps saas

# 等待前端就绪
sleep 30
curl -f http://localhost:3000 || exit 1

# 第三步：重启 Nginx 使配置生效
docker compose -f docker-compose.prod.yml restart nginx

# 第四步：验证全部服务
docker compose -f docker-compose.prod.yml ps
curl http://localhost/          # Nginx 入口
curl http://localhost/health    # 后端健康检查
```

### 11.4 数据库迁移升级

```bash
# 生产环境数据库迁移
docker compose -f docker-compose.prod.yml up -d postgres

# 等待 PostgreSQL 就绪
sleep 15

# 执行迁移（prisma-migrate 会自动执行）
docker compose -f docker-compose.prod.yml up prisma-migrate

# 如自动迁移失败，手动执行
docker compose -f docker-compose.prod.yml run --rm prisma-migrate
# 如果还有问题:
docker compose -f docker-compose.prod.yml exec api python -m prisma migrate dev
```

### 11.5 回退升级

如果升级后发现问题（详见 [回滚指南](#12-回滚指南)），按以下流程降级:

```bash
# 切回旧版镜像
docker compose -f docker-compose.prod.yml pull <旧版标签>
docker compose -f docker-compose.prod.yml up -d --no-deps api saas

# 恢复数据库迁移（如需要）
docker compose -f docker-compose.prod.yml run --rm prisma-migrate rollback

# 验证旧版运行正常
curl http://localhost:8000/health
```

### 11.6 升级注意事项

1. **先 staging 后 production**: 先在 staging 环境验证
2. **避开高峰**: 在访问量低的时间段升级
3. **保留旧镜像**: `docker tag` 保留旧版，以备快速回退
4. **监控升级后指标**: 重点关注错误率和延迟

---

## 12. 回滚指南

### 12.1 版本回退

#### 代码回退

```bash
# 查看 git 历史
git log --oneline -20

# 回退到指定 commit
git revert <commit-hash>  # 安全回退（创建新版本）
# 或者
git checkout <commit-hash>  # 直接检出（不推荐在生产直接使用）

# 重新部署
git push origin main
# Vercel/Railway 自动触发部署
```

#### Docker 镜像回退

```bash
# 方式 1: 使用 tagged 镜像
docker compose -f docker-compose.prod.yml pull zhimeiquan/api:v0.6.0
docker compose -f docker-compose.prod.yml up -d --no-deps api

# 方式 2: 使用 local 旧镜像
docker tag <旧镜像ID> zhimeiquan/api:latest
docker compose -f docker-compose.prod.yml up -d --no-deps api

# 方式 3: 使用 dockerhub 旧版本
docker pull ghcr.io/zhimeiquan/api:0.6.0
```

### 12.2 数据库回滚

```bash
# Prisma 回滚最近一次迁移
docker compose -f docker-compose.prod.yml exec api npx prisma migrate resolve --rolled-back <migration-name>

# 手动回滚 SQL（PostgreSQL）
docker compose -f docker-compose.prod.yml exec postgres psql -U zhimeiquan -d zhimeiquan -f rollback_migration.sql

# 恢复备份数据库
docker exec -i zhimeiquan_postgres_1 psql -U zhimeiquan zhimeiquan < backups/latest/full_backup.sql
```

### 12.3 紧急熔断

当系统出现严重问题时，启用紧急熔断模式:

```bash
# 1. 停止所有非核心服务
docker compose -f docker-compose.prod.yml stop saas prisma-migrate nginx

# 2. 保留后端 API 和健康检查（仅 API）
docker compose -f docker-compose.prod.yml up -d api redis postgres

# 3. 维护页面（可选）
# 将 nginx 代理指向一个静态维护页面
# deploy/nginx/maintenance.conf 提前准备好

# 4. 问题定位后恢复正常
docker compose -f docker-compose.prod.yml up -d
```

### 12.4 回滚检查清单

- [ ] 确认问题影响范围
- [ ] 通知相关团队/用户
- [ ] 执行代码回退
- [ ] 回退 Docker 镜像
- [ ] 回退数据库迁移
- [ ] 验证核心功能恢复
- [ ] 检查日志确认无新错误
- [ ] 通知团队/用户恢复完成

---

## 13. 监控指南

### 13.1 Prometheus + Grafana 监控栈

#### 部署监控栈

```yaml
# deploy/prometheus/prometheus.yml (追加到 docker-compose)
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./deploy/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped
    networks:
      - zhimeiquan-net

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
    restart: unless-stopped
    networks:
      - zhimeiquan-net

volumes:
  prometheus_data:
  grafana_data:
```

```yaml
# deploy/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    metrics_path: '/nginx_status'
```

#### Grafana Dashboard

在 Grafana 中导入 Dashboard JSON（通过 Dashboard → Import → Load JSON）:

```json
{
  "dashboard": {
    "title": "智媒圈总览",
    "panels": [
      {
        "title": "请求总量",
        "expr": "rate(zhimeiquan_requests_total[5m])",
        "type": "graph"
      },
      {
        "title": "错误率",
        "expr": "rate(zhimeiquan_request_errors_total[5m])",
        "type": "graph"
      },
      {
        "title": "P99 延迟",
        "expr": "histogram_quantile(0.99, rate(zhimeiquan_request_duration_ms_bucket[5m]))",
        "type": "graph"
      },
      {
        "title": "LLM 调用分布",
        "expr": "zhimeiquan_llm_calls_total",
        "type": "piechart"
      },
      {
        "title": "缓存命中率",
        "expr": "zhimeiquan_cache_hit_rate",
        "type": "gauge"
      }
    ]
  }
}
```

### 13.2 自监控脚本

项目内置的健康检查可作为简单监控:

```bash
#!/bin/bash
# scripts/healthcheck.sh - 可用于 cron 或 systemd timer
# 每 30 秒执行一次

STATUS_OK=true

# 检查 API
if ! curl -sf http://localhost:8000/health > /dev/null; then
    echo "ERROR: API not healthy" >&2
    STATUS_OK=false
fi

# 检查前端
if ! curl -sf http://localhost:3000 > /dev/null; then
    echo "ERROR: SAAS not healthy" >&2
    STATUS_OK=false
fi

# 检查 Redis
if ! docker exec zhimeiquan_redis_1 redis-cli ping > /dev/null 2>&1; then
    echo "ERROR: Redis not responding" >&2
    STATUS_OK=false
fi

# 检查磁盘空间
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "WARNING: Disk usage at ${DISK_USAGE}%" >&2
fi

if [ "$STATUS_OK" = true ]; then
    echo "ALL SERVICES OK"
else
    # 发送告警（Slack/Webhook）
    curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
         -d '{"text":"智媒圈服务异常！"}'
    exit 1
fi
```

### 13.3 告警通知配置

#### Slack 告警

```yaml
# docker-compose 中追加 Alertmanager
services:
  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./deploy/alertmanager/alertmanager.yml:/etc/prometheus/alertmanager.yml
    networks:
      - zhimeiquan-net
```

#### 微信告警（企业微信）

```python
# scripts/services/alert.py (内置告警服务)
import requests

def send_wechat_alert(title: str, content: str):
    """发送企业微信群机器人告警"""
    webhook = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
    payload = {
        "msgtype": "text",
        "text": {"content": f"[{title}]\n{content}"}
    }
    requests.post(webhook, json=payload, timeout=5)
```

### 13.4 监控指标优先级

| 优先级 | 指标 | 检查方式 | 响应时间 |
|:------:|------|----------|:--------:|
| P0 | 全站不可用 | 主动健康检查 | 立即 |
| P0 | HTTP 5xx > 10% | Prometheus 告警 | 5 分钟内 |
| P1 | 数据库连接失败 | 日志 + 日志检查 | 15 分钟内 |
| P1 | LLM 可用性下降 | Metrics 端点 | 15 分钟内 |
| P2 | 磁盘空间 > 85% | 磁盘监控 | 1 小时内 |
| P2 | 缓存命中率下降 | Metrics 端点 | 1 小时内 |
| P3 | 单个页面加载慢 | 前端监控 | 次日处理 |

---

## 14. 故障排查

### 14.1 服务无法启动

```bash
# 查看所有容器状态
docker compose ps

# 查看详细日志（按服务）
docker compose logs saas --tail=100
docker compose logs api --tail=100
docker compose logs postgres --tail=100
docker compose logs redis --tail=100
docker compose logs nginx --tail=100

# 检查端口占用
netstat -ano | findstr :3000  # Windows
ss -tlnp | grep 3000         # Linux/Mac

# 检查环境变量
docker compose config  # 检查 compose 文件解析
```

### 14.2 数据库问题

```bash
# 连接 PostgreSQL
docker compose exec postgres psql -U zhimeiquan -d zhimeiquan

# 查看连接数
SELECT count(*) FROM pg_stat_activity;

# 查看慢查询
SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

# 清理死锁
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '5 minutes';
```

### 14.3 Redis 问题

```bash
# 连接 Redis
docker compose exec redis redis-cli

# 检查内存
INFO memory

# 检查连接
INFO clients

# 清空所有数据（谨慎！）
FLUSHALL

# 持久化
BGSAVE
```

### 14.4 Nginx 问题

```bash
# 测试配置
docker compose exec nginx nginx -t

# 重载配置
docker compose exec nginx nginx -s reload

# 查看 Nginx 日志
docker compose exec nginx cat /var/log/nginx/access.log
docker compose exec nginx cat /var/log/nginx/error.log

# 检查上游连接
# 确认后端服务可以互相访问
docker compose exec nginx wget -qO- http://saas:3000/
docker compose exec nginx wget -qO- http://api:8000/health
```

### 14.5 磁盘空间不足

```bash
# 查看磁盘使用情况
docker system df
docker volume ls -q | while read vol; do
    echo -n "$vol: "
    docker run --rm -v $vol:/data alpine du -sh /data 2>/dev/null | cut -f1
done

# 清理未使用的镜像
docker image prune -a -f

# 清理日志文件
find /var/lib/docker/containers -name '*.log' -size +100M -exec truncate -s 0 {} \;
```

### 14.6 网络问题

```bash
# 检查容器间网络
docker network ls
docker network inspect zhimeiquan_zhimeiquan-net

# 手动测试 DNS 解析
docker compose exec saas ping api
docker compose exec api ping postgres
docker compose exec api ping redis

# 重置网络
docker compose down
docker network prune -f
docker compose up -d
```

---

## 15. 安全指南

### 15.1 API 密钥轮换

#### 轮换流程

```bash
# 1. 生成新密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. 更新 .env 文件（双写过渡）
# 临时同时设置新旧密钥
DEEPSEEK_API_KEY_OLD=sk-old-key
DEEPSEEK_API_KEY_NEW=sk-new-key
DEEPSEEK_API_KEY=sk-new-key  # 优先使用新密钥

# 3. 重启服务使配置生效
docker compose restart api

# 4. 验证新密钥工作正常
curl http://localhost:8000/health

# 5. 确认无误后移除旧密钥
# 重新编辑 .env 删除 DEEPSEEK_API_KEY_OLD
docker compose restart api
```

#### 各平台轮换操作

| 密钥 | 轮换平台 | 注意事项 |
|------|----------|----------|
| DEEPSEEK_API_KEY | platform.deepseek.com | 旧密钥会立即失效 |
| QWEN_API_KEY | dashscope.console.aliyun.com | 不影响现有调用配额 |
| CLERK_SECRET_KEY | dashboard.clerk.com | 需要重新配置前端环境变量 |
| API_SECRET | 自行生成 | 前后端需要同时更新 |
| STRIPE_SECRET_KEY | dashboard.stripe.com | 旧密钥仍有 24 小时宽限期 |

### 15.2 CORS 安全配置

```python
# 开发环境 - 宽松
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",  # 备用端口
    "http://127.0.0.1:3000",
]

# 生产环境 - 严格
ALLOWED_ORIGINS = [
    os.getenv("FRONTEND_URL", "https://www.zhimeiquan.com"),
]

# 永远不要在 CORS 中使用 "*" 和生产环境的 API_SECRET 混合
```

### 15.3 输入验证加固

```python
# 在 services/validators.py 中确认以下验证已启用:

# 1. 长度限制
CONTENT_LIMITS = {
    "topic_max": 200,           # 主题最大 200 字符
    "body_max": 50000,          # 正文最大 50KB
    "title_max": 50,            # 标题最大 50 字符
    "tags_max": 20,             # 标签最大 20 个
}

# 2. XSS 防护
from services.validators import sanitize_input, strip_html_tags

# 3. SQL 注入防护（Prisma 自动处理 ORM 层）
# 4. 路径遍历防护
from services.validators import validate_safe_path

# 5. 文件上传限制
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "video/mp4"]
```

### 15.4 Docker 网络安全

```yaml
# docker-compose.prod.yml 安全加固
services:
  postgres:
    # 不对外暴露 PostgreSQL 端口（仅内部网络）
    # ports:  # 注释掉这行
    #   - "5432:5432"
    networks:
      - zhimeiquan-net
      # - public-net  # 不要连接到公共网络

  redis:
    # 不对外暴露 Redis 端口
    # ports:  # 注释掉
    #   - "6379:6379"
    command: redis-server --requirepass ${REDIS_PASSWORD}
    networks:
      - zhimeiquan-net

networks:
  zhimeiquan-net:
    driver: bridge
```

### 15.5 日志安全

```python
# 确保敏感信息不被记录到日志中
from services.logging import logger

# 正确做法：记录脱敏信息
logger.info("用户登录成功", user_id=user.id, platform=platform)

# 错误做法：记录密钥
logger.info("API 调用", api_key=api_key)  # 绝对不能这么做
logger.info("请求", body=request_body)  # 可能包含敏感数据
```

### 15.6 定期安全检查

```bash
# 每月执行的安全检查清单

# 1. 检查过期镜像
docker image ls --filter "dangling=true"

# 2. 检查容器特权模式
docker compose ps --format "{{.Name}}: {{.Image}}" | grep -i priv

# 3. 审计环境变量
docker compose exec api printenv | sort

# 4. 检查文件权限
ls -la data/ output/

# 5. 扫描依赖漏洞
pip audit -r scripts/requirements.txt
pnpm audit --prefix saas

# 6. 检查 SSL 证书有效期
echo | openssl s_client -servername your-domain.com -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### 15.7 应急响应流程

```
发现安全问题
    │
    ▼
1. 确认影响范围（哪些用户/数据受影响）
    │
    ▼
2. 紧急措施
   ├── 吊销泄漏的 API 密钥
   ├── 禁用受影响的用户账号
   ├── 限制特定 IP 访问
   └── 暂停受影响的服务
    │
    ▼
3. 修复漏洞
   ├── 代码修复
   ├── 配置加固
   └── 依赖升级
    │
    ▼
4. 恢复服务
   ├── 回滚到安全版本
   ├── 密钥轮换
   └── 逐步恢复
    │
    ▼
5. 事后复盘
   ├── 撰写事故报告
   ├── 更新安全清单
   └── 通知受影响用户（如需）
```
