# 智媒圈 · 爆款内容策略平台

> **不是通用 AI 写作工具** —— 基于 13 个平台实时爆款数据，告诉你每个平台现在什么最火、怎么写更容易爆

![Project Status](https://img.shields.io/badge/status-active-brightgreen)
![Version](https://img.shields.io/badge/version-0.7.0-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![Prisma](https://img.shields.io/badge/Prisma-6.0+-purple)
![Tests](https://img.shields.io/badge/tests-160+passed-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## 为什么选择智媒圈？

| | AI 写作工具<br>(Jasper/Copy.ai) | 社媒管理工具<br>(Sprout Social) | 竞品监控工具<br>(BuzzSumo) | **智媒圈** |
|---|:---:|:---:|:---:|:---:|
| AI 内容生成 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ❌ | ⭐⭐⭐⭐ |
| 平台爆款规则分析 | ❌ | ❌ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 多平台内容分发 | ❌ | ⭐⭐⭐⭐⭐ | ❌ | ⭐⭐⭐⭐ |
| 竞品内容监控 | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 内容质量评分 | ⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 数据闭环优化 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 中国市场适配 | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ |

**一句话：市面上的工具要么帮你"写内容"，要么帮你"管发布"，要么帮你"看数据"——智媒圈把这三件事串成一个闭环。**

## 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层 (Clients)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Web App  │  │  Mobile  │  │   API    │  │  Admin   │   │
│  │ (Next.js) │  │ (PWA)    │  │ (REST)   │  │  Panel   │   │
│  └─────┬─────┘  └──────────┘  └──────────┘  └──────────┘   │
├───────┼─────────────────────────────────────────────────────┤
│       │     代理层 (Proxy / Gateway)                        │
│       │  ┌──────────────────────────────┐                  │
│       └──►  Nginx (反向代理 + SSL)       │                  │
│          └──────────┬───────────────────┘                  │
├─────────────────────┼───────────────────────────────────────┤
│                     │   服务层 (Services)                    │
│  ┌──────────────────┼──────────────────────────────────┐   │
│  │                  ▼                                  │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │         FastAPI Backend (:8000)              │   │   │
│  │  │  ┌─────────┐ ┌──────────┐ ┌────────────┐   │   │   │
│  │  │  │ Routers │ │ Services │ │ Monitors   │   │   │   │
│  │  │  │  (18)   │ │   (18)   │ │  (5)       │   │   │   │
│  │  │  └─────────┘ └──────────┘ └────────────┘   │   │   │
│  │  │  ┌─────────┐ ┌──────────┐ ┌────────────┐   │   │   │
│  │  │  │Auto Eng │ │Analyzers│ │Generators  │   │   │   │
│  │  │  └─────────┘ └──────────┘ └────────────┘   │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                                                    │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │       Next.js Frontend (:3000)               │   │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌────────────┐   │   │   │
│  │  │  │ Pages    │ │Components│ │ API Routes │   │   │   │
│  │  │  │  (12+)   │ │  (15+)   │ │  (24)      │   │   │   │
│  │  │  └──────────┘ └──────────┘ └────────────┘   │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  数据层 (Data Layer)                                 │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │   │
│  │  │PostgreSQL│  │  Redis   │  │ SQLite   │         │   │
│  │  │(生产)     │  │(缓存/限流)│  │(开发)     │         │   │
│  │  └──────────┘  └──────────┘  └──────────┘         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **🔥 爆款规则引擎** | 实时监控 13 个平台热搜/热门内容，AI 分析标题模式、钩子类型、算法变化 |
| **🤖 多模型内容生成** | DeepSeek/Qwen/ERNIE/Hunyuan 多模型路由，基于平台规则生成专属内容 |
| **📊 Fire Score 评分** | 五维评分体系（钩子力/趋势力/互动率/转化力/传播力）+ 贝叶斯实时权重校准 |
| **🔄 内容改写引擎** | 自动优化低分内容至 95+ Fire Score |
| **⚡ 自动化工作流** | 条件-动作引擎（时间/热点/竞品触发） |
| **🕵️ 竞品内容监控** | 对标账号自动追踪 + Playwright 浏览器自动爬取 + 变化趋势分析 |
| **📋 A/B 测试** | 变体管理 + 统计显著性检验 |
| **📡 多平台分发** | 支持 13 个主流平台（抖音/小红书/B站/快手/视频号/公众号/微博/知乎/头条/百度热搜/YouTube/TikTok/Instagram） |
| **📖 知识图谱** | 50+ 专家智能体 + RAG 增强生成 + 9 层知识体系 |
| **🎬 数字人视频** | SiliconFlow 集成 + 多角色预设 |
| **👥 团队协作** | 邀请、分享、角色管理 |
| **💳 订阅计费** | Stripe 三档订阅（¥98/¥168/¥298/月） |

## 与竞品的差异

**智媒圈不是又一个 AI 写作工具。** 市面上有 Jasper/Copy.ai（帮你写）、Sprout Social（帮你发）、BuzzSumo（帮你看）——但没有人把"写、发、看"串成一个闭环。

我们的护城河：
- **13 平台规则引擎**：唯一一个分析短视频/社交平台推荐算法并用于指导内容创作的工具
- **Playwright 浏览器采集**：真正的实时热搜数据，不是买来的第三方 API
- **数据闭环**：发布 → 采集 → 评分 → 优化 → 再发布，内容越做越爆
- **中国市场深度**：从抖音到小红书到B站，不是翻译工具而是原生中文平台

---

## API 路由表（18 组）

| 组 | 端点 | 方法 | 说明 |
|----|------|------|------|
| 健康检查 | `/health` | GET | 服务健康检查 |
| 就绪检查 | `/ready` | GET | 就绪状态（含依赖检查） |
| 内容生成 | `/api/v1/content/generate` | POST | AI 内容生成 |
| 标题生成 | `/api/v1/titles/generate` | POST | AI 标题生成 |
| Fire Score | `/api/v1/score` | POST | 五维评分 |
| 模板 | `/api/v1/templates/list` | GET | 平台模板列表 |
| 模型路由 | `/api/v1/router/profiles` | GET | 模型档案列表 |
| 模型路由 | `/api/v1/router/recommend` | GET | 模型推荐 |
| 模型路由 | `/api/v1/router/chat` | POST | 模型聊天 |
| 分析洞察 | `/api/v1/analytics/overview` | GET | 数据总览 |
| 洞察 | `/api/v1/insights/trends/{platform}` | GET | 平台趋势 |
| 洞察 | `/api/v1/insights/predict/{platform}` | GET | 表现预测 |
| 洞察 | `/api/v1/insights/posting-time/{platform}` | GET | 最佳发布时间 |
| 洞察 | `/api/v1/insights/recommendations` | GET | 内容建议 |
| 视频生成 | `/api/v1/video/generate` | POST | 数字人视频 |
| 图像生成 | `/api/v1/image/generate` | POST | AI 图像生成 |
| 内容评分 | `/api/v1/content/score` | POST | 内容质量评分 |
| 排期管理 | `/api/v1/calendar` | GET/POST | 内容日历 |
| 知识库 | `/api/v1/knowledge` | GET/POST | 知识库管理 |
| 知识库 | `/api/v1/knowledge/list` | GET | 知识库目录树 |
| 知识库 | `/api/v1/knowledge/save` | POST | 知识库保存 |
| 平台规则 | `/api/v1/rules/{platform}` | GET | 平台规则获取 |
| 平台规则 | `/api/v1/rules` | POST | 更新平台规则 |
| A/B 测试 | `/api/v1/ab-test` | POST/GET | A/B 测试管理 |
| A/B 测试 | `/api/v1/ab-test/{testId}` | GET/PUT/DELETE | 单个测试操作 |
| 竞品监控 | `/api/v1/competitors` | GET/POST | 竞品管理 |
| 竞品监控 | `/api/v1/competitors/{id}` | GET/PUT/DELETE | 单个竞品操作 |
| 项目 | `/api/v1/projects` | GET/POST | 项目管理 |
| 项目 | `/api/v1/projects/{id}` | GET/PUT/DELETE | 单个项目操作 |
| 项目 | `/api/v1/projects/{id}/outputs` | GET | 项目输出 |
| 内容改写 | `/api/v1/content/rewrite` | POST | 内容改写优化 |
| 自动化 | `/api/v1/automation` | GET/POST | 工作流管理 |
| 自动化 | `/api/v1/automation/{id}` | PUT/DELETE | 工作流操作 |
| SSO 流式 | `/api/v1/stream/generate` | POST/SSE | 流式内容生成 |
| 数据洞察 | `/api/v1/insights` | GET | 聚合数据洞察 |
| 指标 | `/metrics` | GET | Prometheus 指标 |
| 团队 | `/api/v1/team` | GET/POST | 团队管理 |
| 团队 | `/api/v1/team/invite` | POST | 邀请成员 |
| 智能体 | `/api/v1/agent/start` | POST | 智能体启动 |
| 支付 | `/api/v1/payment/subscribe` | POST | Stripe 订阅 |
| 支付 | `/api/v1/payment/webhook` | POST | Stripe Webhook |
| 前端 API 代理 | `/api/analytics/project/{projectId}` | GET | 项目分析数据 |
| 前端 API 代理 | `/api/monitor/rules` | GET | 监控规则 |

---

## 快速开始

### 前置要求

- Python 3.12+
- Node.js 22+
- pnpm
- Redis 7+（可选，自动降级为内存缓存）

### 后端启动

```bash
cd scripts

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example ../.env
# 编辑 .env，填入 DEEPSEEK_API_KEY 等必要配置

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端启动

```bash
cd saas

# 安装依赖
pnpm install

# Prisma 数据库初始化
pnpm db:generate
pnpm db:push

# 配置环境变量
cp .env.example .env.local
# 编辑 .env.local，填入 Clerk 密钥等

# 启动开发服务器
pnpm dev
```

### 访问

- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 免费爆款报告: http://localhost:3000/reports

---

## 免费资源

### 📊 平台爆款规则分析报告

我们不要求注册就能看到价值：

- [查看](http://localhost:3000/reports) 13 个平台的实时爆款规则分析
- 订阅邮件每周接收最新规则更新
- 数据来源：Playwright 浏览器实时采集 + AI 分析

**示例报告内容**：每个平台的高 CTR 标题公式、钩子类型分布、算法核心参数、当前热门话题、最佳发布时间

---

## Docker 部署

### 开发环境

```bash
docker compose up -d
```

### 生产环境

```bash
# 1. 配置环境变量
cp .env.production.example .env
# 编辑 .env 填入所有密钥

# 2. 启动（Prisma 迁移自动执行）
docker compose -f docker-compose.prod.yml up -d

# 3. 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 4. 手动执行数据库迁移（如需）
docker compose -f docker-compose.prod.yml run --rm prisma-migrate
```

---

## 项目结构

```
智媒圈/
├── scripts/                  # Python 后端 (FastAPI)
│   ├── main.py              # 应用入口
│   ├── middleware.py         # CORS + 中间件
│   ├── routers/             # API 路由 (18 个模块)
│   ├── services/            # 核心服务 (18 个模块)
│   ├── monitors/            # 监控采集器 (5 个模块)
│   ├── analyzers/           # 分析引擎 (校准器, 追踪器)
│   ├── automation/          # 自动化工作流引擎
│   ├── generators/          # 内容改写引擎
│   └── tests/               # 单元测试 (140+)
├── saas/                    # 前端 (Next.js 16)
│   ├── src/
│   │   ├── app/             # 页面 + API 路由
│   │   ├── components/      # 共享组件
│   │   └── lib/             # 工具库
│   ├── prisma/              # Prisma Schema + 迁移
│   └── package.json
├── content/                 # 知识库 (方法论/模板/人设)
│   ├── methodology/         # 10 套方法论
│   ├── templates/           # 13 平台模板
│   ├── experts/             # 50+ 专家人设
│   └── prompts/             # 3 套提示词工程
├── data/                    # 运行时数据
│   ├── rules/               # 13 平台规则
│   ├── analytics/           # 分析数据缓存
│   └── ...
├── deploy/                  # 部署配置
│   ├── nginx/               # Nginx 配置
│   └── scripts/             # 部署脚本
├── docker-compose.yml       # 开发 Docker 配置
├── docker-compose.prod.yml  # 生产 Docker 配置
├── .env.example             # 开发环境变量模板
├── .env.production.example  # 生产环境变量模板
└── README.md                # 本文件
```

---

## 环境变量

| 变量 | 必须 | 默认值 | 说明 |
|------|------|--------|------|
| `DEEPSEEK_API_KEY` | **是** | - | DeepSeek LLM 密钥 |
| `DATABASE_URL` | 是 | `file:./dev.db` | 数据库连接串 |
| `REDIS_URL` | 否 | `redis://localhost:6379` | Redis 连接串 |
| `API_SECRET` | 否 | - | 前后端共享密钥 |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | **是** | - | Clerk 公钥 |
| `CLERK_SECRET_KEY` | **是** | - | Clerk 密钥 |
| `QWEN_API_KEY` | 否 | - | 通义千问密钥 |
| `ERNIE_API_KEY` | 否 | - | 文心一言密钥 |
| `ERNIE_SECRET_KEY` | 否 | - | 文心一言 Secret |
| `HUNYUAN_API_KEY` | 否 | - | 混元密钥 |
| `OPENAI_API_KEY` | 否 | - | OpenAI 密钥 (DALL-E) |
| `STABILITY_API_KEY` | 否 | - | Stability AI 密钥 |
| `SILICONFLOW_API_KEY` | 否 | - | SiliconFlow 密钥 (视频/图像) |
| `STRIPE_SECRET_KEY` | 否 | - | Stripe 密钥 |
| `STRIPE_WEBHOOK_SECRET` | 否 | - | Stripe Webhook 密钥 |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | 否 | - | Stripe 公钥 |
| `LOG_FORMAT` | 否 | `json` | 日志格式 |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别 |
| `DEEPSEEK_BASE_URL` | 否 | `https://api.deepseek.com` | DeepSeek API 地址 |
| `FRONTEND_URL` | 否 | `https://www.zhimeiquan.com` | 前端 URL |
| `ZHIMEIQUAN_CONTENT_DIR` | 否 | `../content` | 知识库路径 |

---

## 技术栈

### 后端
- **框架**: FastAPI 0.115+
- **ORM**: Prisma 6.0+
- **任务调度**: APScheduler 3.10+
- **缓存**: Redis 7+ (自动内存降级)
- **LLM 集成**: DeepSeek / Qwen / ERNIE / Hunyuan
- **支付**: Stripe

### 前端
- **框架**: Next.js 16 + React 19
- **UI**: Tailwind CSS 4 + Radix UI
- **认证**: Clerk
- **测试**: Vitest + Playwright

---

## 测试

```bash
# 后端测试 (Python)
cd scripts
python -m pytest tests/ -v

# 前端测试
cd saas
pnpm test
pnpm test:e2e       # 端到端测试
```

---

## 许可证

MIT
