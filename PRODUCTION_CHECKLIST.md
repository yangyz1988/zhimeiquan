# 智媒圈 生产上线检查清单 v1.0

> **版本**: v0.7.0 | **更新日期**: 2026-07-02
> **状态**: Beta → Production Ready Checklist

---

## 🔴 P0 - 必须完成（上线前 100% 通过）

### 1. 安全与认证
- [ ] **Clerk JWT 鉴权已启用**
  - [ ] 配置 `CLERK_JWT_VERIFICATION_KEY`（PEM 公钥）或 `CLERK_JWKS_URL`
  - [ ] 配置 `CLERK_JWT_ISSUER` 增强验证
  - [ ] 验证未携带 Token 时返回 401
  - [ ] 验证无效 Token 时返回 401
  - [ ] 验证过期 Token 时返回 401

- [ ] **API 密钥安全**
  - [ ] `API_SECRET` 使用强随机密钥（至少 32 位，`openssl rand -hex 32`）
  - [ ] 密钥不提交到 Git（确认 .gitignore 包含 .env）

- [ ] **数据库安全**
  - [ ] PostgreSQL 密码为强密码（16位以上，含大小写+数字+符号）
  - [ ] 数据库只允许内网访问（不暴露公网端口）
  - [ ] 配置每日自动备份（pg_dump + 异地存储）

### 2. 环境配置
- [ ] **环境变量切换为生产值**
  - [ ] `ENV=production`
  - [ ] `FRONTEND_URL` 为正式域名
  - [ ] `NEXT_PUBLIC_APP_URL` 为正式域名
  - [ ] 所有 API Key 切换为正式 Key（非 test）

- [ ] **Prisma Schema 切换到 PostgreSQL**
  - [ ] 注释掉 sqlite provider
  - [ ] 启用 postgresql provider
  - [ ] `DATABASE_URL` 指向 PostgreSQL
  - [ ] 执行 `prisma migrate deploy` 初始化生产数据库

### 3. 构建与部署验证
- [ ] **前端生产构建通过**
  ```bash
  cd saas && pnpm build
  ```
  - [ ] 无 TypeScript 错误
  - [ ] 无 ESLint 严重错误

- [ ] **后端依赖安装完成**
  ```bash
  cd scripts && pip install -r requirements.txt
  ```

- [ ] **Docker 生产环境启动成功**
  ```bash
  docker compose -f docker-compose.prod.yml up -d
  ```
  - [ ] 所有容器健康检查通过
  - [ ] `/health` 返回 200
  - [ ] `/ready` 返回 200
  - [ ] `/docs` 可访问

### 4. 核心流程冒烟测试
- [ ] **用户注册/登录**（Clerk 正常跳转）
- [ ] **创建项目 → 生成内容**
- [ ] **Fire Score 评分正常返回**
- [ ] **内容改写功能正常**
- [ ] **知识库创建与搜索**
- [ ] **A/B 测试创建与运行**
- [ ] **数据看板正常加载**

---

## 🟠 P1 - 强烈建议（上线后 1 周内补齐）

### 5. 限流与防护
- [ ] **全局限流生效**
  - [ ] 验证超过 60 次/分钟返回 429
  - [ ] 响应头包含 `X-RateLimit-*` 字段
  - [ ] 按用户维度限流（而非全局）

- [ ] **CORS 配置收紧**
  - [ ] 生产环境只允许正式域名
  - [ ] 移除 localhost 白名单

### 6. 可观测性
- [ ] **日志采集**
  - [ ] 结构化 JSON 日志输出
  - [ ] 接入日志平台（ELK / Loki / 云厂商日志服务）

- [ ] **监控告警**
  - [ ] `/metrics` 端点接入 Prometheus / Grafana
  - [ ] 设置关键告警：错误率 > 5%、响应时间 > 3s、服务宕机
  - [ ] 数据库连接数、CPU、内存监控

### 7. 数据完整性
- [ ] **Prisma 迁移验证**
  - [ ] 生产数据库迁移无报错
  - [ ] 所有表和索引正确创建
  - [ ] 种子数据（UserPlan 套餐）已导入

- [ ] **Redis 缓存验证**
  - [ ] Redis 连接正常
  - [ ] 限流数据写入 Redis
  - [ ] Redis 不可用时自动降级内存缓存

---

## 🟡 P2 - 优化项（上线后迭代）

### 8. 性能优化
- [ ] **数据库索引审查** - 高频查询字段是否都有索引
- [ ] **慢查询监控** - 记录超过 1s 的 SQL
- [ ] **静态资源 CDN** - 前端静态资源上 CDN
- [ ] **Gzip 压缩** - Nginx 启用 gzip/brotli

### 9. 高可用
- [ ] **后端多实例部署**（至少 2 个实例）
- [ ] **负载均衡** - Nginx / ALB 分发请求
- [ ] **数据库主从复制** - 读请求走从库
- [ ] **健康检查自动重启** - Docker restart_policy

### 10. 合规与安全增强
- [ ] **HTTPS 强制跳转**
- [ ] **安全响应头**（HSTS、X-Frame-Options、CSP）
- [ ] **隐私政策 & 用户协议** 页面
- [ ] **用户数据导出/删除** 功能（GDPR 合规）

---

## 🔧 部署操作步骤

### 方式一：Docker Compose 一键部署（推荐）

```bash
# 1. 克隆代码
git clone <your-repo> && cd zhimeiquan

# 2. 配置生产环境变量
cp .env.production.example .env
# 编辑 .env，填入所有密钥和域名

# 3. 切换 Prisma 到 PostgreSQL
# 编辑 saas/prisma/schema.prisma，启用 postgresql provider

# 4. 启动服务
docker compose -f docker-compose.prod.yml up -d

# 5. 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 6. 验证健康状态
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

### 方式二：手动部署

```bash
# 后端
cd scripts
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 前端
cd saas
pnpm install
pnpm build
pnpm start -p 3000

# Nginx 反向代理（见 deploy/nginx/）
```

---

## 📋 本次升级新增内容

### 新增文件
- `scripts/services/auth.py` - Clerk JWT 鉴权服务
- `scripts/services/metrics.py` - 指标收集器

### 修改文件
- `scripts/main.py` - 移除旧 API Key 中间件，统一走新鉴权；增强 metrics 和 health 端点
- `scripts/middleware.py` - 新增鉴权中间件 + 限流中间件 + 请求指标统计
- `scripts/requirements.txt` - 新增 PyJWT 依赖
- `scripts/services/cache.py` - 已有 RateLimiter，新增全局限流中间件调用
- `.env.example` - 新增 Clerk JWT 配置项
- `.env.production.example` - 新增 Clerk JWT + 限流配置
- `saas/prisma/schema.prisma` - 添加 PostgreSQL 切换注释

### 新增能力
1. ✅ **Clerk JWT 用户鉴权** - 支持 PEM 公钥和 JWKS 两种验证模式
2. ✅ **按用户/IP 维度限流** - 滑动窗口算法，Redis/内存双模式
3. ✅ **真实 Prometheus 风格指标** - 请求量、错误率、响应耗时统计
4. ✅ **生产环境 CORS 自动收紧** - ENV=production 时自动移除 localhost
5. ✅ **增强健康检查** - /health + /ready 分离

---

## ⚠️ 已知风险与注意事项

1. **Clerk 鉴权开发模式**：未配置 CLERK_SECRET_KEY 时自动降级为 mock 用户，生产环境必须配置
2. **Prisma 切换**：从 sqlite 切到 postgresql 需要重新生成 client 和执行迁移，已有数据无法自动迁移
3. **限流粒度**：当前为全局限流，后续可按接口级别细分不同限流策略
4. **Metrics 内存存储**：当前指标存在内存中，重启后清零；生产环境建议接入 Prometheus

---

## ✅ 验收标准

满足以下全部条件，可判定为 **生产就绪**：

- [ ] P0 检查项 100% 完成
- [ ] 核心用户旅程 5 条全部跑通
- [ ] 连续运行 24 小时无崩溃
- [ ] 错误率 < 1%
- [ ] 平均响应时间 < 500ms
- [ ] 安全扫描无高危漏洞
- [ ] 数据库备份验证可用

---

*检查清单由系统自动生成，每次部署前请逐项核对并打勾*
