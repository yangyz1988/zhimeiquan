# 智媒圈 (AI内容策略引擎)

> 12平台实时监控 × 多模型协作 × 数据驱动决策 — 一站式 AI 内容策略平台

## 核心特性

### 内容生产
- **多模型协作** - DeepSeek / Qwen / ERNIE / Hunyuan 智能路由
- **Fire Score 5 维评分** - hook / trust / retention / conversion / emotion
- **8 大爆款钩子** - 数字型/反常识型/痛点型/利益型/悬念型/对比型/情绪型/权威型
- **3 种人设** - 学长/学姐/专家，匹配不同平台调性
- **一键生成** - 选题 → 大纲 → 标题 → 正文 → 视频

### 数据驱动
- **12 平台实时监控** - 抖音/小红书/B站/微博/知乎/头条/快手/YouTube/TikTok/公众号/视频号/百度热搜
- **数据闭环** - 自动追踪每篇内容表现，识别高 ROI 模式
- **A/B 测试** - 多版本内容自动分组测试
- **自动优化** - 基于历史数据微调生成策略

### 视频能力
- **AI 文案 → 视频** - Edge TTS 配音 + SRT 字幕 + 自动封面
- **3 大图像生成** - DALL-E / Stability / SiliconFlow
- **多语种支持** - 中文/英文/日文等

### 协作 + 变现
- **团队协作** - 多角色（管理员/编辑/审稿）+ 共享项目
- **调度中心** - 一次/周期性发布调度（APScheduler）
- **智能体自治** - AutonomousAgent 自动监控 + 分析 + 调整
- **Stripe 支付** - 基础 ¥49 / Pro ¥99 / 企业 ¥199 三档订阅
- **模板市场** - 内置 4 套爆款模板（教程/评测/观点/Vlog）

### 工程化
- **生产级稳定性** - 3 次重试 + 指数退避 + 熔断器 + Redis 限流
- **结构化日志** - JSON 输出 + 慢请求追踪
- **输入验证** - XSS 清洗 + 长度限制 + JSON 大小
- **全链路测试** - 156 个自动化测试（Python 126 + Vitest 30）
- **CI/CD** - GitHub Actions + Docker Compose + Vercel

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js 16 + React 19 + Tailwind CSS 4 + shadcn/ui |
| 后端 | Python 3.11 + FastAPI + Pydantic + APScheduler |
| 数据库 | Prisma 6 + SQLite (dev) / PostgreSQL (prod) |
| 缓存 | Redis 7 (限流 + 响应缓存) |
| 认证 | Clerk 7.4 |
| 支付 | Stripe |
| LLM | DeepSeek / Qwen / ERNIE / Hunyuan |
| 部署 | Vercel + Railway + Docker + Nginx |

## 快速开始

### 本地开发

```bash
# 1. 克隆
git clone <repo> && cd zhimeiquan

# 2. 后端
cd scripts
pip install -r requirements.txt
cp .env.example .env  # 填写 DEEPSEEK_API_KEY 等
uvicorn main:app --reload --port 8000

# 3. 前端
cd ../saas
pnpm install
cp .env.example .env.local  # 填写 Clerk + DATABASE_URL
pnpm db:push
pnpm dev
```

访问 http://localhost:3000

### Docker 一键启动

```bash
docker compose up -d
```

启动 4 个服务：
- `saas` - Next.js 前端 (port 3000)
- `api` - FastAPI 后端 (port 8000)
- `redis` - 缓存 + 限流 (port 6379)
- `nginx` - 反向代理 (port 80)

## 部署到生产

详见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

- **Vercel** 部署 Next.js（推荐）
- **Railway** 部署 FastAPI + Redis
- **Docker Compose** 自托管

## 项目结构

```
zhimeiquan/
├── saas/                  # Next.js 前端
│   ├── src/
│   │   ├── app/           # 页面 + API 路由
│   │   │   ├── api/       # Next.js API（项目 CRUD）
│   │   │   ├── (auth)/    # 鉴权页（sign-in/sign-up）
│   │   │   ├── analytics/ # 数据分析
│   │   │   ├── calendar/  # 内容日历
│   │   │   ├── dashboard/ # 用户工作台
│   │   │   ├── generate/  # 内容生成
│   │   │   ├── monitor/   # 爆款监控
│   │   │   └── router/    # 模型路由
│   │   ├── components/    # React 组件
│   │   └── lib/           # 工具
│   ├── e2e/               # Playwright E2E
│   └── prisma/            # 数据库 schema
├── scripts/               # Python 后端
│   ├── services/          # 业务服务（20+）
│   ├── routers/           # API 路由（13）
│   ├── monitors/          # 平台监控
│   ├── tests/             # pytest 测试（126）
│   ├── main.py            # FastAPI 入口
│   └── middleware.py      # 请求日志中间件
├── content/               # 知识库（方法论/模板/人设）
├── docs/                  # 文档
├── deploy/                # 部署配置
└── docker-compose.yml     # 4 服务编排
```

## API 文档

启动后访问 http://localhost:8000/docs 查看 Swagger UI

13 个路由组：
- `/api/v1/content` - 内容生成
- `/api/v1/titles` - 标题生成
- `/api/v1/score` - Fire Score 评分
- `/api/v1/rules` - 爆款规则
- `/api/v1/video` - 视频生成
- `/api/v1/image` - 图像生成
- `/api/v1/analytics` - 数据分析
- `/api/v1/ab_test` - A/B 测试
- `/api/v1/calendar` - 内容日历
- `/api/v1/templates` - 模板
- `/api/v1/agent` - 智能体
- `/api/v1/team` - 团队协作
- `/api/v1/router` - 模型路由

## 测试

```bash
# 后端
cd scripts && python -m pytest tests/ -v

# 前端
cd saas && pnpm test

# 端到端
cd saas && pnpm test:e2e

# 覆盖率
cd scripts && python -m pytest --cov=services --cov=routers
cd saas && pnpm test:coverage
```

## 环境变量

### 后端 (scripts/.env)
- `DEEPSEEK_API_KEY` - DeepSeek LLM
- `QWEN_API_KEY` / `ERNIE_API_KEY` + `ERNIE_SECRET_KEY` / `HUNYUAN_API_KEY` - 多模型
- `REDIS_URL` - Redis 连接
- `LOG_FORMAT` - `json` / `text`
- `LOG_LEVEL` - `info` / `debug` / `warning`

### 前端 (saas/.env.local)
- `DATABASE_URL` - PostgreSQL / SQLite
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` + `CLERK_SECRET_KEY` - 认证
- `NEXT_PUBLIC_API_URL` - 后端 API 地址
- `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` - 支付
- `OPENAI_API_KEY` / `STABILITY_API_KEY` / `SILICONFLOW_API_KEY` - 图像

## 性能

- 平均响应时间 < 2.5s（DeepSeek 评分）
- Redis 缓存命中率 60-80%
- 并发支持 100+ QPS
- 12 平台并行采集 < 30s

## 安全

- 输入验证（XSS 清洗 + 长度限制）
- Redis 限流（默认 30 req/60s 滑动窗口）
- 熔断器（连续 5 次失败自动断开 30s）
- 密钥全部走 .env，零硬编码
- Clerk JWT 鉴权

## 路线图

- [ ] 抖音/小红书真实发布 API 集成
- [ ] 视频自动剪辑（FFmpeg + 模板）
- [ ] 多语言 i18n
- [ ] 移动端 App（React Native）
- [ ] 私有模型微调

## License

MIT
