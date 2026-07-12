# 智媒圈 部署指南

> **版本**: v0.7.0 | **日期**: 2026-07-01

---

## 部署前检查清单

- [x] 代码优化完成
- [x] 测试文件补充完成
- [x] 安全漏洞修复（22→1，剩余 postcss 为间接依赖）
- [x] 版本号对齐（v0.7.0）
- [x] Docker 配置就绪

---

## 部署方式

### 方式一：Docker 部署（推荐）

#### 1. 准备环境变量

`ash
cd \"D:\\oc  mooz\\智媒圈\"

# 复制生产环境模板
copy .env.production.example .env

# 编辑 .env，填入必要的密钥：
# - DEEPSEEK_API_KEY（必须）
# - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY（必须）
# - CLERK_SECRET_KEY（必须）
# - POSTGRES_PASSWORD（必须）
# - API_SECRET（必须）
`

#### 2. 启动服务

`powershell
# 构建并启动所有服务
docker compose -f docker-compose.prod.yml up -d --build

# 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f
`

#### 3. 验证部署

`powershell
# 检查健康状态
curl http://localhost:8000/health
curl http://localhost:3000

# 或者用 PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health
Invoke-WebRequest -Uri http://localhost:3000
`

---

### 方式二：手动部署

#### 后端部署

`powershell
cd \"D:\\oc  mooz\\智媒圈\\scripts\"

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
`

#### 前端部署

`powershell
cd \"D:\\oc  mooz\\智媒圈\\saas\"

# 安装依赖
pnpm install

# 生成 Prisma Client
pnpm db:generate

# 构建
pnpm build

# 启动
pnpm start
`

---

### 方式三：云平台部署

#### Vercel 部署（前端）

1. 推送代码到 GitHub
2. 在 Vercel 中导入项目
3. 设置 Root Directory 为 saas
4. 配置环境变量

#### Railway 部署（后端）

1. 推送代码到 GitHub
2. 在 Railway 中导入项目
3. 设置 Root Directory 为 scripts
4. 配置环境变量

---

## 必需的环境变量

| 变量 | 说明 | 来源 |
|------|------|------|
| DEEPSEEK_API_KEY | LLM API 密钥 | https://platform.deepseek.com |
| NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY | Clerk 公钥 | https://dashboard.clerk.com |
| CLERK_SECRET_KEY | Clerk 密钥 | https://dashboard.clerk.com |
| POSTGRES_PASSWORD | 数据库密码 | 自定义 |
| API_SECRET | API 密钥 | openssl rand -hex 32 |

---

## 常见问题

### Docker 启动失败
- 检查 .env 文件是否配置完整
- 检查 Docker Desktop 是否运行
- 查看日志：docker compose logs

### 前端无法连接后端
- 检查 API_URL 环境变量
- 检查 API_SECRET 是否前后端一致

### 数据库连接失败
- 检查 DATABASE_URL 格式
- PostgreSQL 需要先运行 pnpm db:migrate

---

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80/443 | 反向代理 |
| 前端 | 3000 | Next.js |
| 后端 | 8000 | FastAPI |
| Redis | 6379 | 缓存 |
| PostgreSQL | 5432 | 数据库 |

---

*部署指南完成*
