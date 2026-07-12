# 智媒圈 架构说明

> 版本: 0.7.0 | 更新日期: 2026-06-27

---

## 目录

1. [整体架构](#1-整体架构)
2. [核心数据流](#2-核心数据流)
3. [模块依赖关系](#3-模块依赖关系)
4. [护城河设计](#4-护城河设计)
5. [扩展指南](#5-扩展指南)
6. [技术栈明细](#6-技术栈明细)

---

## 1. 整体架构

### 1.1 组件图（Component Diagram）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            智媒圈 系统架构图                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Client Layer (用户层)                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │    │
│  │  │ Web App      │  │ PWA/Mobile   │  │ Third-party Apps     │   │    │
│  │  │ Next.js 16   │  │ Browser      │  │ Batch / Import APIs  │   │    │
│  │  │ :3000        │  │              │  │                      │   │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │    │
│  └─────────┼─────────────────┼─────────────────────┼───────────────┘    │
│            │                 │                     │                     │
│            ▼                 ▼                     ▼                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                   Gateway Layer (网关层)                          │    │
│  │  ┌─────────────────────────────────────────────────────────┐   │    │
│  │  │  Nginx (反向代理 + SSL + 路由 + 限流)                    │   │    │
│  │  │  Port :80/:443                                          │   │    │
│  │  │                                                         │   │    │
│  │  │  /api/*     ──► api:8000  (FastAPI)                     │   │    │
│  │  │  /*         ──► saas:3000  (Next.js)                    │   │    │
│  │  │  /ws/*      ──► saas:3000  (WebSocket/SSE)              │   │    │
│  │  └─────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│            │                                                             │
│            ├──────────────┬──────────────┬───────────────────┐          │
│            ▼              ▼              ▼                     ▼          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ SaaS Service │ │   API Service│ │  Monitor     │ │  Worker      │   │
│  │ (Next.js)    │ │ (FastAPI)    │ │  (Scraper)   │ │  (Jobs)      │   │
│  │              │ │              │ │              │ │              │   │
│  │ Pages:       │ │ Route Layer: │ │ Platforms:   │ │ Triggers:    │   │
│  │ ├─ Dashboard │ │ ├─ health    │ │ ├─ 抖音      │ │ ├─ cron      │   │
│  │ ├─ Generate  │ │ ├─ content   │ │ ├─ 小红书    │ │ ├─ hot_trend │   │
│  │ ├─ Analyze   │ │ ├─ titles    │ │ ├─ B站       │ │ └─ webhook   │   │
│  │ ├─ Team      │ │ ├─ score     │ │ ├─ YouTube   │ │              │   │
│  │ ├─ Agent     │ │ ├─ fire-scope│ │ ├─ TikTok    │ │ ┌──────────┐ │   │
│  │ └─ Admin     │ │ └─ stream    │ │ └─ ...       │ │ │Scheduler │ │   │
│  │              │ │              │ │              │ │ │APScheduler│ │   │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘   │
│         │                │                 │                │            │
│         │                ▼                 │                │            │
│         │         ┌──────────────┐        │                │            │
│         │         │  Service     │        │                │            │
│         │         │  Layer       │        │                │            │
│         │         │              │        │                │            │
│         │         │ Router       │◄───────┘                │            │
│         │         │ (ModelSel)   │                         │            │
│         │         │ Cache        │                         │            │
│         │         │ Prompts      │                         │            │
│         │         │ DataLoop     │                         │            │
│         │         │ Analytics    │                         │            │
│         │         │ SchedulerSvc │                         │            │
│         │         │ Validators   │                         │            │
│         │         │ Metrics      │                         │            │
│         │         └──────┬───────┘                         │            │
│         │                │                                 │            │
│         │                ▼                                 │            │
│         │         ┌──────────────┐                         │            │
│         │         │  Engine      │                         │            │
│         │         │  Layer       │                         │            │
│         │         │              │                         │            │
│         │         │ Automation   │                         │            │
│         │         │ (Workflow)   │                         │            │
│         │         │              │                         │            │
│         │         │ Rewriter     │                         │            │
│         │         │ (Iterative)  │                         │            │
│         │         │              │                         │            │
│         │         │ Agent        │                         │            │
│         │         │ (Auto-Matrix)│                         │            │
│         │         └──────┬───────┘                         │            │
│         │                │                                 │            │
│         │                ▼                                 │            │
│         │         ┌──────────────┐                         │            │
│         │         │  Analyzer    │                         │            │
│         │         │  Layer       │                         │            │
│         │         │              │                         │            │
│         │         │ FireScore    │                         │            │
│         │         │ Calibrator   │                         │            │
│         │         │ (Bayesian)   │                         │            │
│         │         │              │                         │            │
│         │         │ DataTracker  │                         │            │
│         │         └──────┬───────┘                         │            │
│         │                │                                 │            │
│         └────────────────┼─────────────────────────────────┘            │
│                          │                                             │
│                          ▼                                             │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                    Data Access Layer                         │      │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │      │
│  │  │PostgreSQL│ │ SQLite   │ │  Redis   │ │  JSON Files    │  │      │
│  │  │ (Main DB)│ │(Calibr.) │ │ (Cache)  │ │ (Analytics)    │  │      │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │      │
│  │  ┌──────────┐ ┌──────────┐                                   │      │
│  │  │S3/本地   │ │ Git Repo │                                   │      │
│  │  │(Media)  │ │(Content) │                                   │      │
│  │  └──────────┘ └──────────┘                                   │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                          │                                             │
│                          ▼                                             │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                    External Services                         │      │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────┐    │      │
│  │  │DeepSeek│ │ Qwen   │ │Ernie   │ │Hunyuan │ │OpenAI   │    │      │
│  │  │(Primary)│ │(Backup)│ │(Scoring)│ │(Creative)│ │(DALL-E)│    │      │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └─────────┘    │      │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                 │      │
│  │  │Clerk   │ │Stripe  │ │Silicon  │ │平台API │                 │      │
│  │  │(Auth)  │ │(Pay)   │ │Flow     │ │(采集)  │                 │      │
│  │  └────────┘ └────────┘ │(Video) │ └────────┘                 │      │
│  │                       └────────┘                             │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流图：内容生成

```
用户提交请求
    │
    │  topic, platform, persona, duration
    ▼
┌─────────────────────────┐
│  Router Layer           │
│  POST /content/generate │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐     ┌─────────────────────┐
│  Validator Service      │────►│  Input Sanitization │
│  - 主题合法性           │     │  - 长度限制         │
│  - 平台白名单           │     │  - XSS 过滤         │
│  - 时长范围             │     │  - HTML 清洗        │
└───────────┬─────────────┘     └─────────────────────┘
            │
            ▼
┌─────────────────────────┐
│  Cache Lookup           │
│  (key: topic+platform+  │
│   persona+duration)     │
│                         │
│  ┌─────────┐  ┌──────┐ │
│  │ HIT     │  │ MISS │ │
│  │ 直接返回 │  │ 继续 │ │
│  └─────────┘  └──┬───┘ │
└───────────────────┼─────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│  Prompt Builder Service                             │
│                                                     │
│  加载知识库内容:                                     │
│  ├─ 平台模板 (content/templates/)                   │
│  ├─ 专家人设 (content/experts/)                     │
│  ├─ 方法论 (content/methodology/)                   │
│  └─ 实时爆款规则 (data/rules/{platform}.json)       │
│                                                     │
│  组装系统提示词:                                     │
│  system = [方法论指导] + [平台特性] + [人设约束]     │
│  user   = [用户主题] + [格式要求]                   │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│  Model Router (智能调度)                            │
│                                                     │
│  决策流程:                                          │
│  1. 根据 TaskType 筛选候选模型                      │
│  2. 按策略 (cost/quality/speed) 排序               │
│  3. 检查历史成功率 (>95% 才可用)                   │
│  4. 选择最优模型                                    │
│                                                     │
│  当前首选: deepseek   (性价比最佳)                  │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│  LLM Service                                        │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  DeepSeek Chat API                            │  │
│  │  ├─ system prompt (知识库注入)                │  │
│  │  ├─ user prompt (topic + 格式化指令)         │  │
│  │  └─ response_format: JSON                     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  容错机制:                                          │
│  - 超时 15s → 切换到备选模型                        │
│  - 格式错误 → 二次重试 + 修正 prompt                │
│  - 全部失败 → 返回降级模板                          │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│  Response Parser                                    │
│                                                     │
│  解析 LLM JSON 输出:                                │
│  ├─ titles[]        (3-5 个标题选项)               │
│  ├─ script          (正文内容)                     │
│  ├─ subtitles       (摘要/短文案)                  │
│  ├─ tags[]          (话题标签)                     │
│  ├─ hook            (开头金句)                     │
│  └─ cta             (行动号召)                     │
│                                                     │
│  格式校验:                                          │
│  - 必需字段完整性                                   │
│  - 平台字数限制                                     │
│  - 内容安全检测                                     │
└──────────────────────────┬──────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Cache Store │  │  Data Loop   │  │  Stream Out  │
│  (Redis 1h)  │  │  (analytics) │  │  (SSE)       │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ▼
                    返回给用户
```

### 1.3 数据流图：Fire Score 校准

```
阶段 1: 初始评分                              阶段 2: 数据采集
                                             │
用户提交内容   ┌──────────────┐               │
title/body    ─►Prompts.build│  ──LLM──►    │
platform      │  (五维标准)   │  结构化评分   │
              └──────┬───────┘               │
                     │                       │
                     ▼                       ▼
              ┌──────────────┐      ┌──────────────┐
              │Model Router  │      │返回评分结果   │
              │→ ernie(评分) │      │hook/trust/   │
              └──────┬───────┘      │retention/    │
                     │              │conversion/   │
                     ▼              │emotion/      │
              ┌──────────────┐      │total_score   │
              │解析 JSON     │      └──────┬───────┘
              │评分结构      │             │
              └──────┬───────┘             ▼
                     │           ┌────────────────┐
                     ▼           │用户发布到平台  │
              ┌──────────────┐   │  (手动/API)   │
              │返回前端展示   │   └──────┬───────┘
              │分数+等级+    │          │
              │改写建议      │          ▼
              └──────────────┘   ┌────────────────┐
                                 │互动数据回流      │
                                 │views/likes/     │
                                 │comments/shares  │
                                 └──────┬───────┘
                                        │
                                        ▼
                              阶段 3: 校准更新
                                        │
                              ┌────────────────┐
                              │POST /fire-score│
                              │/report          │
                              │(performance)    │
                              └──────┬───────┘
                                     │
                ┌────────────────────┼────────────────────┐
                ▼                    ▼                    ▼
         ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
         │DataTracker   │   │Calibrator    │   │SQLite DB     │
         │record_publish│   │record_perf() │   │tracker.db   │
         │update_metrics│   └──────┬───────┘   └──────────────┘
         └──────────────┘          │
                │                  ▼
                │          ┌──────────────┐
                │          │calibrate()   │
                │          │              │
                │          │1.取最近50条  │
                │          │2.算Pearson   │
                │          │3.重分配权重  │
                │          │4.写入DB      │
                │          └──────┬───────┘
                │                 │
                ▼                 ▼
         ┌──────────────┐   ┌──────────────┐
         │JSON记录      │   │weight_configs│
         │(analytics/)  │   │表(更新后权重)│
         └──────────────┘   └──────┬───────┘
                                  │
                                  ▼
                          ┌──────────────┐
                          │新权重生效     │
                          │下次评分使用   │
                          │更精准的评分   │
                          └──────────────┘
```

### 1.4 模块依赖树

```
智媒圈项目依赖树
│
├── scripts/ (后端核心)
│   ├── main.py                  [FastAPI 入口]
│   │   ├── middleware.py        [CORS, Auth, Timing]
│   │   │   ├── validators.py
│   │   │   └── error_codes.py
│   │   │
│   │   ├── routers/             [18 组 API 路由]
│   │   │   ├── health.py        → middleware, error_codes
│   │   │   ├── content.py       → services/prompts, services/router,
│   │   │   │                    │  services/cache, services/scheduler_service,
│   │   │   │                    │  services/validators
│   │   │   ├── titles.py        → services/deepseek, services/prompts,
│   │   │   │                    │  services/scheduler_service
│   │   │   ├── score.py         → services/router, services/prompts,
│   │   │   │                    │  services/scheduler_service
│   │   │   ├── fire_score.py    → analyzers/calibrator, analyzers/data_tracker
│   │   │   ├── rules.py         → monitors/scheduler
│   │   │   ├── analytics.py     → services/data_loop
│   │   │   ├── ab_test.py       → services/data_loop (ABTester)
│   │   │   ├── calendar.py      → services/scheduler_service
│   │   │   ├── agent.py         → services/agent
│   │   │   ├── team.py          → services/team
│   │   │   ├── video.py         → services/video, services/digital_human
│   │   │   ├── image.py         → services/image_gen
│   │   │   ├── templates.py     → services/templates
│   │   │   ├── model_router.py  → services/router
│   │   │   ├── insights.py      → services/insights
│   │   │   ├── competitors.py   → monitors/competitor
│   │   │   ├── stream.py        → services/router, services/prompts,
│   │   │   │                    │  services/cache, services/validators,
│   │   │   │                    │  services/deepseek
│   │   │   └── knowledge.py     → services/knowledge_graph
│   │   │
│   │   ├── services/            [核心业务逻辑]
│   │   │   ├── cache.py         → redis (可选, 内存降级)
│   │   │   ├── metrics.py       → prometheus_client
│   │   │   ├── logging.py       → structlog / logging
│   │   │   ├── models.py        [LLM 基类]
│   │   │   ├── deepseek.py      → models, cache, error_handler, logging
│   │   │   ├── router.py        → models, cache, metrics, logging
│   │   │   ├── prompts.py       → services/content_loader
│   │   │   ├── content_loader.py→ 文件系统 (content/ 目录)
│   │   │   ├── scheduler_service.py → apscheduler
│   │   │   ├── data_loop.py     → 文件系统 (data/analytics/)
│   │   │   ├── validators.py    → 纯 Python (无外部依赖)
│   │   │   ├── error_codes.py   → 纯 Python
│   │   │   ├── error_handler.py → error_codes, logging
│   │   │   ├── insights.py      → monitors/analyzer, monitors/scraper
│   │   │   ├── templates.py     → 文件系统
│   │   │   ├── team.py          → 文件系统
│   │   │   ├── agent.py         → services/data_loop, services/video,
│   │   │   │                    │  services/scheduler_service
│   │   │   ├── video.py         → 文件系统
│   │   │   ├── digital_human.py → httpx (SiliconFlow API)
│   │   │   ├── image_gen.py     → httpx (DALL-E/Stability/SiliconFlow)
│   │   │   ├── knowledge_graph.py→ 文件系统
│   │   │   ├── payment.py       → stripe
│   │   │   └── metrics.py       → prometheus_client
│   │   │
│   │   ├── monitors/            [数据采集]
│   │   │   ├── scraper.py       → httpx, BeautifulSoup
│   │   │   ├── analyzer.py      → numpy, scipy
│   │   │   ├── scheduler.py     → apscheduler, scraper, analyzer
│   │   │   └── competitor.py    → scraper, httpx
│   │   │
│   │   ├── analyzers/           [分析引擎]
│   │   │   ├── calibrator.py    → sqlite3, numpy, scipy
│   │   │   └── data_tracker.py  → 文件系统 (data/analytics/)
│   │   │
│   │   ├── generators/          [生成引擎]
│   │   │   └── rewriter.py      → services/router, services/prompts
│   │   │
│   │   └── automation/          [自动化引擎]
│   │       └── engine.py        → services/agent, services/data_loop,
│   │                            │  services/scheduler_service
│   │
│   └── tests/                   [140+ 测试用例]
│       ├── test_api.py
│       ├── test_services.py
│       ├── test_cache.py
│       ├── test_validators.py
│       ├── test_router.py
│       └── ...
│
├── saas/ (前端核心)
│   ├── package.json             [Next.js 16 + React 19]
│   ├── prisma/
│   │   ├── schema.prisma        [数据模型定义]
│   │   └── migrations/          [数据库迁移]
│   ├── src/
│   │   ├── app/                 [Pages + API Routes]
│   │   │   ├── (dashboard)/     [仪表板路由组]
│   │   │   ├── (auth)/          [认证路由组 (Clerk)]
│   │   │   ├── api/             [Next.js API 代理]
│   │   │   │   └── proxy/[...path] → http://api:8000/$path
│   │   │   └── layout.tsx       [根布局]
│   │   ├── components/          [UI 组件]
│   │   │   ├── ui/              [Radix UI 基础组件]
│   │   │   ├── content/         [内容生成相关]
│   │   │   ├── analytics/       [数据可视化]
│   │   │   └── agent/           [Agent 矩阵]
│   │   └── lib/                 [工具库]
│   │       ├── clerk.ts         [Clerk 客户端]
│   │       └── api.ts           [API 客户端封装]
│   │
│   └── tailwind.config.ts       [样式配置]
│
├── content/                     [知识库 - Git 管理]
│   ├── methodology/             [10 套方法论]
│   ├── templates/               [13 平台模板]
│   ├── experts/                 [50+ 专家人设]
│   └── prompts/                 [3 套提示词工程]
│
├── data/                        [运行时数据 - JSON]
│   ├── analytics/               [内容表现]
│   ├── rules/                   [爆款规则]
│   ├── workflows/               [自动化定义]
│   └── ...
│
├── output/                      [校准数据]
│   └── tracker.db               [SQLite - Fire Score]
│
├── deploy/                      [部署配置]
│   ├── nginx/                   [Nginx 配置]
│   └── scripts/                 [部署脚本]
│
├── docker-compose.yml           [开发环境]
├── docker-compose.prod.yml      [生产环境]
└── .env.example                 [环境变量模板]
```

---

## 2. 核心数据流

### 内容生成流

（已在上方 1.2 节完整展示）

### Fire Score 评分流

```
用户提交内容 (title, body, platform)
       │
       ▼
┌─────────────────────┐
│  Prompts.score()    │ ← 注入五维评分标准
│  - 知识库方法论       │    钩子力/信任度/完播力/
│  - 平台爆款规则       │    转化力/情绪值
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Model Router       │ ← 优先选择 ernie (结构化评分)
│  → 调用 LLM         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  JSON 解析          │ ← hook/trust/retention/
│                     │    conversion/emotion/total
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  返回评分结果         │ ← 分数 + 等级 + 建议 + 分析
│  + 改写建议          │
└─────────────────────┘
```

### 数据闭环流（Fire Score 校准）

（已在上方 1.3 节完整展示）

### 自动化工作流流

```
用户创建自动化工作流
       │
       ▼
┌─────────────────────────────────────────────────────┐
│  工作流定义:                                         │
│  Trigger (触发器) → Actions (多个动作)                │
│                                                     │
│  触发器类型:                                         │
│  - TimeTrigger:     cron 表达式定时触发               │
│  - HotTopicTrigger: 热榜匹配关键词时触发              │
│  - PerformanceTrigger: 指标低于阈值时触发             │
│  - ScheduleTrigger: 指定时间点触发                    │
│                                                     │
│  动作类型:                                           │
│  - GenerateAction:  生成新内容                       │
│  - RewriteAction:   改写现有内容                     │
│  - PublishAction:   发布内容到平台                   │
│  - NotifyAction:    发送通知                         │
│  - AnalyzeAction:   执行数据分析                     │
└─────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  Engine 定时检查:                            │
│  - 每分钟检查所有活跃工作流                    │
│  - 调用 Trigger.evaluate(context)            │
│  - 触发 → 按序执行所有 Actions               │
│  - 记录执行结果和统计                          │
└─────────────────────────────────────────────┘
       │
       ▼
    内容生成 / 改写 / 发布 / 通知
```

---

## 3. 模块依赖关系

### 分层依赖原则

```
路由层 (routers) → 只能调用 服务层(services) + 引擎层(analyzers/generators/automation)
服务层 (services) → 只依赖其他 services + LLM clients
监控层 (monitors) → 独立运行，被路由层调度
引擎层 → 可调用 services 和 monitors
分析层 → 独立于其他层 (自有数据存储)
生成层 → 可调用 services (router/prompts/cache)
```

（详细依赖树见上方 1.4 节）

---

## 4. 护城河设计

### 护城河 1: Fire Score 实时校准算法

**核心价值:** 不是静态评分，而是基于用户实际发布数据的贝叶斯权重校准引擎。

**技术实现:**
```python
# 先验权重 (默认)
DEFAULT_WEIGHTS = {
    "hook": 25.0,        # 钩子力
    "trust": 20.0,       # 信任度
    "retention": 25.0,   # 完播力
    "conversion": 15.0,  # 转化力
    "emotion": 15.0,     # 情绪值
}

# 校准算法:
# 1. 收集用户每一篇内容的五维评分 + 实际互动率
# 2. 计算每维分数与互动率的皮尔逊相关系数
# 3. 高相关性 → 高权重 (该维度对实际表现影响大)
# 4. 数据积累越多 → 评分越精准 → 形成数据网络效应
```

**为什么是护城河:**
- 竞争对手可以复制评分界面，但无法复制每个用户的校准数据
- 用户使用越多 → 数据积累越多 → 评分越准 → 切换成本越高
- 每个用户每平台有独立的权重配置，个性化程度极高

### 护城河 2: 知识体系的内容系统工程

**核心价值:** 九层知识体系 + 50+ 专家人设 + 多平台模板 = 可编程的内容知识图谱。

**组成:**
- 10 套方法论文档（Hook/Trust/Retention/Conversion/Emotion + 方法)
- 13 个平台模板（含算法偏好和爆款规则）
- 50+ 专家人设（不同领域和风格）
- 3 套提示词工程（系统提示/分步推理/平台适配）

**为什么是护城河:**
- 知识库不是简单文档，而是结构化的向量检索系统
- 竞品需要大量内容领域知识积累才能达到同等质量
- 知识库随着使用不断优化，形成正反馈

### 护城河 3: 多模型路由智能调度

**核心价值:** 基于成本-质量-速度-A/B 结果的综合最优决策引擎。

```python
# 模型档案
MODEL_PROFILES = {
    "deepseek": {cost: 0.001, latency: 2500ms, quality: 0.90, best_for: [content, analysis]},
    "qwen":     {cost: 0.003, latency: 2000ms, quality: 0.85, best_for: [content, title, translation]},
    "ernie":    {cost: 0.004, latency: 1800ms, quality: 0.82, best_for: [scoring, analysis]},
    "hunyuan":  {cost: 0.005, latency: 2200ms, quality: 0.83, best_for: [creative, chat]},
}

# 路由决策: 自动选择满足质量门槛的最便宜模型
# 历史学习: 记录每次调用的结果, 自动优化路由策略
```

**为什么是护城河:**
- 竞品可以接入多个模型，但路由决策引擎是积累出来的
- 历史数据越多，推荐越精准，成本越低
- 自动降级和熔断保障服务稳定性

### 护城河 4: 数据闭环网络效应

**核心价值:** 每个用户的内容表现数据都回馈到系统中，形成跨用户的数据网络。

**数据流:**
```
用户发布内容 → 平台互动数据 → 回传系统
                         ↓
                脱敏聚合 + 趋势分析
                         ↓
    行业洞察报告 ← 内容机会发现 ← 最佳模式分析
                         ↓
                所有用户受益 (预测更准)
```

**为什么是护城河:**
- 用户越多 → 数据越多 → 预测越准 → 用户粘性越强
- 竞品从零开始无法短期积累同等量级的分析数据
- 网络效应形成正循环，后来者难以追赶

### 护城河 5: 自动化矩阵运营系统

**核心价值:** 从"单个内容生成"到"多账号矩阵的全自动运营"。

**能力:**
- 自主 Agent 支持多账号矩阵管理
- 自动选题 → 生成 → 审核 → 发布 → 分析 → 优化迭代
- 工作流引擎支持复杂的条件-动作自动化
- 矩阵运营统计 + 智能优化建议

**为什么是护城河:**
- 完整的自动化矩阵运营系统构建复杂，竞品短期难以复制
- Agent 的模板和策略是经过多轮迭代优化的
- 矩阵数据积累形成跨账号的内容策略知识

---

## 5. 扩展指南

### 5.1 如何添加新平台？

**步骤:**

1. **添加平台规则文件** — 在 `data/rules/` 创建 `{平台名}.json`
   ```json
   {
     "platform": "新平台",
     "title_rules": [{"rule": "标题规则说明"}],
     "hook_patterns": [{"type": "钩子类型", "count": 0}],
     "trending_topics": [],
     "best_practices": []
   }
   ```

2. **添加平台模板** — 在 `content/templates/` 创建模板文件
   ```markdown
   # 新平台内容模板
   ## 算法特点
   ## 内容结构
   ## 爆款公式
   ```

3. **添加到平台白名单** — 在 `services/validators.py` 中:
   ```python
   VALID_PLATFORMS = [
       "抖音", "小红书", ..., "新平台",
   ]
   ```

4. **添加规则采集器** — 在 `monitors/scheduler.py` 中注册:
   ```python
   self.rules_sources = {
       "抖音": self._fetch_douyin_rules,
       ...
       "新平台": self._fetch_new_platform_rules,
   }
   ```

5. **添加爆款规则注入** — 在 `services/prompts.py` 中补充平台特点:
   ```python
   system += f"\n- 新平台：特点说明\n"
   ```

### 5.2 如何添加新模型？

**步骤:**

1. **创建 LLM 客户端** — 在 `services/` 创建 `new_model.py`
   ```python
   class NewModelClient(BaseLLM):
       async def chat(self, prompt, system="", **kwargs):
           # 实现与 NewModel API 的通信
           ...
   ```

2. **注册模型** — 在 `services/models.py` 中:
   ```python
   MODELS = {
       ...
       "new_model": NewModelClient,
   }
   ```

3. **添加模型档案** — 在 `services/router.py` 中:
   ```python
   MODEL_PROFILES["new_model"] = ModelProfile(
       name="New Model Name",
       cost_per_1k_tokens=0.002,
       avg_latency_ms=2000,
       quality_score=0.88,
       max_tokens=4096,
       best_for=[TaskType.CONTENT_GENERATION, TaskType.CHAT],
   )
   ```

4. **添加提示词优化** — 在 `router.py` 的 `enhance_prompt` 方法中添加模型特有优化规则

5. **配置环境变量** — 在 `.env` 中添加:
   ```
   NEW_MODEL_API_KEY=your_key_here
   ```

6. **更新路由策略** — 可选，调整 `select_cheapest_model` 的优先级

### 5.3 如何添加新引擎？

**步骤:**

1. **创建引擎目录和文件**
   ```
   scripts/
   ├── new_engine/           # 新引擎目录
   │   ├── __init__.py
   │   └── core.py          # 核心逻辑
   ```

2. **在 `main.py` 中注册新的路由**
   ```python
   from routers import new_router
   app.include_router(new_router.router, prefix="/api/v1/new-engine", tags=["新引擎"])
   ```

3. **创建路由文件** `routers/new_engine.py`
   ```python
   from fastapi import APIRouter
   from services.new_engine import NewEngineService
   router = APIRouter()
   ```

4. **集成到现有系统**（可选）
   - 如果新引擎需要定时运行，在 `monitors/scheduler.py` 添加定时任务
   - 如果需要知识库支持，接入 `services/knowledge_graph.py`
   - 如果需要缓存，使用 `services/cache.py`
   - 如果需要数据追踪，接入 `services/data_loop.py`

---

## 6. 技术栈明细

### 后端

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | FastAPI | 0.115+ | Python Web 框架 |
| 服务器 | Uvicorn | - | ASGI 服务器 |
| LLM | DeepSeek | - | 主要模型(便宜+高质量) |
| LLM | 通义千问 | - | 备用模型 |
| LLM | 文心一言 | - | 评分优化(结构化输出强) |
| LLM | 混元 | - | 创意类任务 |
| 图像 | DALL-E 3 | - | OpenAI 图像生成 |
| 图像 | Stability AI | - | 开源图像生成 |
| 视频 | SiliconFlow | - | 数字人视频生成 |
| 缓存 | Redis | 7+ | 内存数据库 (自动降级) |
| 调度 | APScheduler | 3.10+ | 定时任务 |
| 支付 | Stripe | - | 三档订阅 |
| 日志 | 结构化日志 | - | JSON 格式 + 性能追踪 |
| 指标 | Prometheus | - | 文本格式导出 |
| 测试 | Pytest | - | 140+ 测试用例 |

### 前端

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | Next.js | 16 | React 全栈框架 |
| UI | Tailwind CSS | 4 | 原子化 CSS |
| 组件 | Radix UI | - | 无障碍组件库 |
| 图表 | Chart.js | 4 | 数据可视化 |
| 认证 | Clerk | - | 用户身份管理 |
| ORM | Prisma | 6.0+ | 数据库 ORM |
| 测试 | Vitest | - | 单元测试 |
| E2E | Playwright | - | 端到端测试 |

### 基础设施

| 类别 | 技术 | 说明 |
|------|------|------|
| 容器化 | Docker + Compose | 两套配置 (dev/prod) |
| 反向代理 | Nginx | 路由 + SSL + SSE |
| CI/CD | GitHub Actions | 自动测试 + 部署 |
| 数据库(开发) | SQLite | 文件数据库 |
| 数据库(生产) | PostgreSQL 16 | 关系数据库 |
