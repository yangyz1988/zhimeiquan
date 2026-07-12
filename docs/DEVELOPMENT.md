# 智媒圈 开发指南

> 版本: 0.7.0 | 更新日期: 2026-06-27

---

## 目录

1. [环境搭建](#1-环境搭建)
2. [项目结构详解](#2-项目结构详解)
3. [代码规范](#3-代码规范)
4. [Git 工作流](#4-git-工作流)
5. [提交规范](#5-提交规范)
6. [测试指南](#6-测试指南)
7. [本地调试技巧](#7-本地调试技巧)

---

## 1. 环境搭建

### 前置要求

| 工具 | 最低版本 | 验证命令 |
|------|----------|----------|
| Python | 3.12+ | `python --version` |
| Node.js | 22+ | `node --version` |
| pnpm | 9+ | `pnpm --version` |
| Docker (可选) | 24+ | `docker --version` |
| Redis (可选) | 7+ | `redis-cli --version` |

### 一分钟快速启动

```bash
# 1. 克隆并进入项目
cd 智媒圈

# 2. 后端环境
cd scripts
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate
pip install -r requirements.txt
cd ..

# 3. 前端环境
cd saas
pnpm install
cd ..

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 5. 启动服务（两个终端窗口）
# 终端 1:
cd scripts && uvicorn main:app --reload --port 8000
# 终端 2:
cd saas && pnpm dev
```

### 完整环境配置

#### 后端依赖

核心依赖 (`requirements.txt`):
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
httpx>=0.27.0
redis>=5.0.0
apscheduler>=3.10.0
numpy>=1.26.0
scipy>=1.13.0
pydantic>=2.0.0
python-multipart>=0.0.9
pytest>=8.0.0
pytest-asyncio>=0.24.0
```

#### 前端依赖

核心依赖 (`package.json`):
```json
{
  "dependencies": {
    "next": "16",
    "react": "19",
    "@prisma/client": "6",
    "@clerk/nextjs": "^6",
    "@radix-ui/*": "^1",
    "chart.js": "^4",
    "lucide-react": "^0.400"
  }
}
```

### IDE 推荐配置

**VS Code 推荐插件:**
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- ESLint (dbaeumer.vscode-eslint)
- Prettier (esbenp.prettier-vscode)
- Tailwind CSS IntelliSense (bradlc.vscode-tailwindcss)
- Prisma (Prisma.prisma)

**VS Code settings.json 建议:**
```json
{
  "python.defaultInterpreterPath": "scripts/venv/Scripts/python.exe",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "files.associations": {
    "*.css": "tailwindcss"
  }
}
```

---

## 2. 项目结构详解

### 2.1 顶层目录概览

```
智媒圈/                          # 项目根目录
├── scripts/                     # Python 后端 (FastAPI)
├── saas/                        # 前端 (Next.js)
├── content/                     # 知识库 (Git 管理的内容资产)
├── data/                        # 运行时数据 (JSON 文件)
├── output/                      # 分析产出 (SQLite)
├── deploy/                      # 部署相关配置
├── docs/                        # 项目文档
├── .env.example                 # 环境变量模板 (开发)
├── .env.production.example      # 环境变量模板 (生产)
├── docker-compose.yml           # Docker 开发环境
├── docker-compose.prod.yml      # Docker 生产环境
├── dev-start.ps1                # 开发环境一键启动脚本
├── start.ps1                    # 生产环境一键启动脚本
└── README.md                    # 项目说明
```

### 2.2 scripts/ 后端目录结构

这是项目的核心业务逻辑所在，采用分层架构。

```
scripts/
├── main.py                     # FastAPI 应用工厂 + 路由注册 + 中间件挂载
├── middleware.py               # CORS 配置 + API Key 验证 + 请求计时
├── requirements.txt            # Python 依赖
├── Dockerfile                  # 后端容器镜像构建
│
├── routers/                    # API 路由层 (薄 - 只做参数解析和响应)
│   ├── __init__.py
│   ├── health.py               # GET /health, GET /ready
│   ├── content.py              # POST /content/generate (核心)
│   ├── titles.py               # POST /titles/generate
│   ├── score.py                # POST /score/generate
│   ├── fire_score.py           # POST /fire-score/ + POST /fire-score/report
│   ├── rules.py                # 爆款规则管理 (GET/POST/refresh)
│   ├── analytics.py            # 内容表现分析
│   ├── ab_test.py              # A/B 测试管理
│   ├── calendar.py             # 内容日历/调度
│   ├── agent.py                # 自主 Agent (创建/列表/矩阵)
│   ├── team.py                 # 团队协作 (团队/邀请/分享)
│   ├── video.py                # 视频生成
│   ├── image.py                # 图像生成
│   ├── templates.py            # 模板 CRUD
│   ├── model_router.py         # 模型路由管理 (策略/统计/切换)
│   ├── insights.py             # 内容洞察报告
│   ├── competitors.py          # 竞品监控
│   ├── stream.py               # SSE 流式生成端点
│   └── knowledge.py            # 知识库管理
│
├── services/                   # 服务层 (厚 - 核心业务逻辑)
│   ├── __init__.py
│   ├── prompts.py              # 提示词构建器 (注入知识库内容)
│   ├── content_loader.py       # 知识库文件加载器 (Markdown/JSON)
│   ├── models.py               # LLM 客户端抽象基类 (BaseLLM)
│   ├── deepseek.py             # DeepSeek API 客户端
│   ├── router.py               # 智能模型路由器 (cost/quality/speed 策略)
│   ├── cache.py                # 缓存服务 (Redis + 内存降级)
│   ├── scheduler_service.py    # APScheduler 集成 (定时任务管理)
│   ├── data_loop.py            # 数据闭环 (内容表现追踪)
│   ├── insights.py             # 洞察引擎 (聚合分析)
│   ├── templates.py            # 模板管理服务
│   ├── team.py                 # 团队服务
│   ├── agent.py                # Agent 服务 (自主任务编排)
│   ├── video.py                # 视频生成服务
│   ├── digital_human.py        # 数字人视频服务
│   ├── image_gen.py            # 图像生成服务 (DALL-E/Stability)
│   ├── knowledge_graph.py      # 知识图谱构建
│   ├── payment.py              # Stripe 支付集成
│   ├── validators.py           # 输入验证 (安全第一)
│   ├── metrics.py              # Prometheus 指标收集
│   ├── logging.py              # 结构化日志 (JSON 格式)
│   ├── error_handler.py        # 错误处理 (重试/熔断)
│   └── error_codes.py          # 统一错误码体系
│
├── monitors/                   # 监控采集层 (独立运行)
│   ├── __init__.py
│   ├── scraper.py              # 多平台数据采集 (多源降级策略)
│   ├── analyzer.py             # 爆款规则分析 (聚类/趋势)
│   ├── scheduler.py            # 定时采集调度
│   └── competitor.py           # 竞品账号追踪
│
├── analyzers/                  # 分析引擎层
│   ├── __init__.py
│   ├── calibrator.py           # Fire Score 贝叶斯校准
│   └── data_tracker.py         # 数据追踪记录
│
├── generators/                 # 生成引擎层
│   ├── __init__.py
│   └── rewriter.py             # 迭代式内容改写
│
├── automation/                 # 自动化引擎层
│   ├── __init__.py
│   └── engine.py               # 条件-动作工作流引擎
│
└── tests/                      # 测试目录 (140+ 测试用例)
    ├── test_api.py             # API 集成测试
    ├── test_services.py        # 服务单元测试
    ├── test_cache.py           # 缓存测试
    ├── test_validators.py      # 验证器测试
    ├── test_router.py          # 路由策略测试
    ├── test_data_loop.py       # 数据闭环测试
    ├── test_scraper.py         # 采集器测试
    ├── test_content_loader.py  # 知识库加载测试
    ├── test_error_handler.py   # 错误处理测试
    ├── test_models.py          # 模型测试
    ├── test_video.py           # 视频生成测试
    ├── test_new_modules.py     # 新模块测试
    └── fix_end.py              # 测试修复工具
```

### 2.3 saas/ 前端目录结构

```
saas/
├── package.json                # 依赖 + 脚本
├── next.config.ts              # Next.js 配置 (代理/MDX/压缩)
├── tailwind.config.ts          # Tailwind CSS 配置
├── tsconfig.json               # TypeScript 配置
├── Dockerfile                  # 前端容器镜像构建
├── prisma/
│   ├── schema.prisma           # 数据模型 + 数据源
│   └── migrations/             # Prisma 迁移文件
│       └── 20260626xxxx_init/
│           └── migration.sql
│
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # 根布局 (Providers, Header, Footer)
│   │   ├── page.tsx            # 首页 (仪表板)
│   │   │
│   │   ├── (dashboard)/        # 仪表板路由组 (认证守卫)
│   │   │   ├── page.tsx        # 仪表板主页
│   │   │   ├── generate/       # 内容生成页
│   │   │   │   └── page.tsx
│   │   │   ├── analyze/        # 数据分析页
│   │   │   │   └── page.tsx
│   │   │   ├── agent/          # Agent 矩阵页
│   │   │   │   └── page.tsx
│   │   │   ├── team/           # 团队协作页
│   │   │   │   └── page.tsx
│   │   │   └── admin/          # 管理后台
│   │   │       └── page.tsx
│   │   │
│   │   ├── (auth)/             # 认证路由组 (Clerk)
│   │   │   ├── sign-in/
│   │   │   └── sign-up/
│   │   │
│   │   ├── api/                # Next.js API Routes (代理/边缘函数)
│   │   │   └── proxy/
│   │   │       └── [...path]/  # 反向代理到后端 FastAPI
│   │   │           └── route.ts
│   │   │
│   │   └── globals.css         # 全局样式
│   │
│   ├── components/             # React 组件
│   │   ├── ui/                 # 基础 UI 组件 (Radix UI + Tailwind)
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Dialog.tsx
│   │   │   └── Table.tsx
│   │   │
│   │   ├── content/            # 内容相关组件
│   │   │   ├── ContentForm.tsx     # 内容生成表单
│   │   │   ├── TitleCard.tsx       # 标题卡片
│   │   │   ├── ScriptPreview.tsx   # 脚本预览
│   │   │   └── ScoreDisplay.tsx    # 评分展示
│   │   │
│   │   ├── analytics/          # 数据分析组件
│   │   │   ├── ChartPanel.tsx        # 图表面板 (Chart.js)
│   │   │   ├── MetricCard.tsx        # 指标卡片
│   │   │   └── TrendLine.tsx         # 趋势线
│   │   │
│   │   ├── agent/              # Agent 组件
│   │   │   ├── AgentMatrix.tsx       # Agent 矩阵视图
│   │   │   ├── WorkflowCard.tsx      # 工作流卡片
│   │   │   └── QueueStatus.tsx       # 队列状态
│   │   │
│   │   └── layout/             # 布局组件
│   │       ├── Sidebar.tsx
│   │       ├── Header.tsx
│   │       └── Breadcrumb.tsx
│   │
│   └── lib/                    # 工具库
│       ├── api.ts              # API 客户端封装 (fetch 统一处理)
│       ├── clerk.ts            # Clerk 客户端工具
│       ├── constants.ts        # 全局常量
│       └── utils.ts            # 通用工具函数
│
└── tests/                      # 前端测试 (Vitest + Playwright)
    ├── unit/
    └── e2e/
```

### 2.4 content/ 知识库目录结构

知识库是智媒圈的「知识底盘」，所有方法论、模板、人设、提示词都在这里。

```
content/
├── methodology/            # 10 套方法论
│   ├── hook.md             # 钩子理论 (7 种钩子模式)
│   ├── trust.md            # 信任建立 (权威/共情/证据)
│   ├── retention.md        # 完播策略 (节奏/悬念/信息密度)
│   ├── conversion.md       # 转化设计 (CTA/漏斗/路径)
│   ├── emotion.md          # 情绪价值 (共鸣/愤怒/惊喜)
│   ├── pacing.md           # 节奏控制 (开头/中段/结尾)
│   ├── storytelling.md     # 故事结构 (英雄之旅/三段式)
│   ├── viral.md            # 病毒传播 (模因/趋势/裂变)
│   ├── seo.md              # 搜索优化 (关键词/标题/标签)
│   └── platform_fit.md     # 平台适配 (算法偏好/分发机制)
│
├── templates/              # 13 个平台模板
│   ├── 抖音.md
│   ├── 小红书.md
│   ├── B站.md
│   ├── 微博.md
│   ├── 知乎.md
│   ├── 头条.md
│   ├── 快手.md
│   ├── YouTube.md
│   ├── TikTok.md
│   ├── 公众号.md
│   ├── 视频号.md
│   ├── 百度热搜.md
│   └── Instagram.md
│
├── experts/                # 50+ 专家人设 (按领域分类)
│   ├── tech/               # 科技领域
│   │   ├── ai_researcher.md
│   │   └── product_manager.md
│   ├── finance/            # 金融领域
│   ├── lifestyle/          # 生活方式
│   └── ...
│
└── prompts/                # 3 套提示词工程
    ├── system_prompts.md   # 系统提示词规范
    ├── chain_of_thought.md # 分步推理模板
    └── platform_adapt.md   # 平台适配模板
```

### 2.5 deploy/ 部署配置目录

```
deploy/
├── nginx/
│   ├── default.conf            # 默认代理配置
│   └── ssl.conf                # SSL 配置 (生产)
├── prometheus/
│   └── prometheus.yml          # Prometheus 抓取配置
├── alertmanager/
│   └── alertmanager.yml        # 告警路由配置
└── scripts/
    ├── backup.sh               # 数据备份脚本
    ├── deploy.sh               # 部署脚本
    └── healthcheck.sh          # 健康检查脚本
```

### 2.6 关键架构原则

1. **前后端分离**: 前端 Next.js (:3000)、后端 FastAPI (:8000)，通过 Nginx 统一入口
2. **路由层薄**: `routers/` 只负责参数解析和响应返回，业务逻辑在 `services/`
3. **服务层厚**: `services/` 包含所有核心业务逻辑
4. **引擎独立**: `analyzers/`、`generators/`、`automation/` 各自独立，可被路由层调用
5. **知识库外置**: `content/` 目录独立管理，通过 Git 版本控制
6. **多源降级**: 数据采集、模型调用、缓存均有降级方案
7. **结构化日志**: 所有日志使用 JSON 格式，方便集中收集和查询

---

## 3. 代码规范

### 3.1 Python 规范

**遵循 PEP 8，项目特有约定:**

```python
# 1. 导入顺序: 标准库 → 第三方 → 项目内部
import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.router import default_router, TaskType
from services.logging import logger


# 2. 类型注解: 所有函数必须标注类型
async def generate_content(
    topic: str,
    platform: str = "抖音",
    duration: int = 60,
) -> dict:
    """文档字符串: 描述功能、参数和返回值"""
    ...


# 3. 类命名: PascalCase
class FireScoreCalibrator:
    ...


# 4. 函数命名: snake_case
def calculate_engagement_rate(views: int, likes: int) -> float:
    ...


# 5. 常量命名: UPPER_CASE
DEFAULT_WEIGHTS: dict[str, float] = {
    "hook": 25.0,
    "trust": 20.0,
}
```

### 3.2 路由文件规范

每个路由文件遵循统一结构:

```python
"""路由模块说明文档字符串"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.xxx import XxxService

router = APIRouter()
service = XxxService()


class XxxRequest(BaseModel):
    field: str = "default"


class XxxResponse(BaseModel):
    field: str


@router.post("/endpoint", response_model=XxxResponse)
async def endpoint(req: XxxRequest):
    """端点说明"""
    try:
        result = await service.do_something(req.field)
        return XxxResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail="操作失败")
```

### 3.3 错误处理规范

```python
# 正确: 使用统一错误码
from services.error_codes import raise_error

raise_error("CONT003")  # → 400: "主题不能为空"

# 正确: 使用 AppError 包装
from services.error_codes import AppError

raise AppError("SERV001", message_override="自定义消息")

# 错误: 直接 raise HTTPException
raise HTTPException(status_code=400, detail="主题不能为空")  # 不推荐
```

### 3.4 日志规范

```python
from services.logging import logger

# 正确: 使用结构化字段
logger.info("内容生成成功", topic=topic[:30], platform=platform, model=model_name)

# 正确: 错误信息加 traceback
logger.exception("发布失败", content_id=content_id)

# 错误: 使用 print()
print("内容生成成功")  # 不推荐

# 错误: 字符串拼接字段
logger.info(f"内容生成成功: {topic} on {platform}")  # 不推荐
```

### 3.5 前端代码规范

```typescript
// 组件命名: PascalCase
export function ContentForm() { ... }

// Hooks: camelCase with use prefix
function useContentState() { ... }

// Props: interface 定义
interface ContentFormProps {
  onSubmit?: (data: FormData) => void;
  disabled?: boolean;
}

// 常量: UPPER_SNAKE_CASE
const MAX_DURATION = 300;

// API 调用: 使用统一的 api 客户端
import { api } from '@/lib/api';
const result = await api.post('/content/generate', { topic, platform });
```

---

## 4. Git 工作流

### 4.1 分支策略

```
main (生产)                    ← 始终可部署，受保护分支
├── staging (预发布)           ← 集成测试，稳定可用
├── develop (开发主干)         ← 功能集成的主分支
│   ├── feat/user-auth         ← 新功能: 用户认证
│   ├── feat/fire-score-v2     ← 新功能: Fire Score V2
│   ├── fix/login-bug          ← 修复: 登录问题
│   └── refactor/cache-layer   ← 重构: 缓存层
```

**分支命名规范:**

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feat/` | 新功能 | `feat/streaming-output` |
| `fix/` | Bug 修复 | `fix/title-length-limit` |
| `refactor/` | 重构 | `refactor/router-cache` |
| `docs/` | 文档更新 | `docs/add-ops-guide` |
| `test/` | 测试相关 | `test/add-validator-tests` |
| `chore/` | 构建/配置 | `chore/update-deps` |
| `hotfix/` | 紧急修复 | `hotfix/auth-overflow` |

### 4.2 日常开发流程

```bash
# 1. 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feat/my-feature

# 2. 开发过程中频繁提交
git add .
git commit -m "feat: 实现内容生成功能"

# 3. 保持与 develop 同步
git fetch origin
git rebase origin/develop

# 4. 推送到远程
git push origin feat/my-feature

# 5. 发起 Pull Request
#    → Target: develop
#    → 填写 PR 描述和影响范围
#    → 等待代码审查

# 6. PR 合并后
git checkout develop
git pull origin develop
git branch -d feat/my-feature  # 删除本地分支
```

### 4.3 发布流程 (main/staging)

```bash
# 1. 从 develop 创建发布分支
git checkout develop
git pull origin develop
git checkout -b release/v0.7.0

# 2. 更新版本号
# 修改 package.json / main.py 中的 version

# 3. 更新 CHANGELOG.md

# 4. 合并到 staging 进行集成测试
git checkout staging
git merge release/v0.7.0

# 5. staging 测试通过后，合并到 main
git checkout main
git merge staging
git tag v0.7.0

# 6. 推送到远程
git push origin main --tags
git push origin staging

# 7. 触发 CI/CD (GitHub Actions / Vercel / Railway)
```

### 4.4 代码审查 Checklist

- [ ] 代码通过 `pytest` 测试 (`cd scripts && python -m pytest tests/ -v`)
- [ ] 新增功能有对应的测试用例
- [ ] 类型注解完整
- [ ] 文档字符串已更新
- [ ] 没有硬编码的敏感信息
- [ ] 日志使用结构化格式
- [ ] 错误使用统一错误码
- [ ] API 变更更新了 API 文档
- [ ] 前端组件有 TypeScript 类型
- [ ] 没有遗留的 `console.log` 或 `print()`

### 4.5 Commit Message 规范

**格式:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type):**

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `docs` | 文档更新 |
| `chore` | 构建/工具/配置 |
| `style` | 代码风格 |
| `perf` | 性能优化 |

**范围 (scope):**

| 范围 | 说明 |
|------|------|
| `api` | 后端 API |
| `engine` | 引擎 |
| `monitor` | 监控采集 |
| `saas` | 前端 |
| `docker` | Docker 配置 |
| `deploy` | 部署 |
| `content` | 知识库 |

**示例:**
```
feat(api): 添加 SSE 流式内容生成端点

实现 POST /api/v1/stream/generate，支持实时推送生成进度。
包含: 标题流式输出、脚本段落逐步推送、完整结果合并。

Close #123
```

---

## 5. 测试指南

### 5.1 测试架构

```
tests/
├── test_api.py              # API 集成测试 (FastAPI TestClient)
├── test_services.py         # 服务层单元测试
├── test_cache.py            # 缓存服务测试
├── test_validators.py       # 输入验证测试
├── test_router.py           # 模型路由测试
├── test_data_loop.py        # 数据闭环测试
├── test_templates.py        # 模板服务测试
├── test_team.py             # 团队服务测试
├── test_scraper.py          # 采集器测试
├── test_content_loader.py   # 知识库加载测试
├── test_error_handler.py    # 错误处理测试
├── test_models.py           # 模型测试
├── test_video.py            # 视频生成测试
├── test_new_modules.py      # 新模块测试
└── fix_end.py               # 测试修复
```

### 5.2 运行测试

```bash
# 运行全部测试
cd scripts
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_api.py -v

# 运行特定测试函数
python -m pytest tests/test_api.py::test_health -v

# 带覆盖率报告
python -m pytest tests/ --cov=. --cov-report=term

# 并行运行
python -m pytest tests/ -v -x  # -x: 遇到第一个失败就停止
```

### 5.3 编写测试规范

```python
"""测试模板"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestContentAPI:
    """内容 API 测试组"""

    def test_generate_success(self):
        """测试内容生成成功"""
        response = client.post(
            "/api/v1/content/generate",
            json={"topic": "AI 工具", "platform": "抖音", "persona": "学长型", "duration": 60},
        )
        assert response.status_code == 200
        data = response.json()
        assert "titles" in data
        assert "script" in data

    def test_generate_invalid_topic(self):
        """测试空主题返回 400"""
        response = client.post(
            "/api/v1/content/generate",
            json={"topic": "", "platform": "抖音", "persona": "学长型", "duration": 60},
        )
        assert response.status_code == 400

    def test_generate_invalid_platform(self):
        """测试无效平台返回 400"""
        response = client.post(
            "/api/v1/content/generate",
            json={"topic": "AI", "platform": "无效平台", "persona": "学长型", "duration": 60},
        )
        assert response.status_code == 400
```

### 5.4 测试覆盖要求

| 模块 | 最低覆盖率 | 说明 |
|------|:---------:|------|
| services/validators.py | 90% | 安全相关必须高覆盖 |
| services/cache.py | 80% | 缓存逻辑 |
| services/error_codes.py | 90% | 错误码体系 |
| services/error_handler.py | 80% | 错误处理 |
| services/data_loop.py | 70% | 数据闭环 |
| services/router.py | 70% | 模型路由 |
| routers/*.py | 60% | API 路由层 |
| analyzers/calibrator.py | 70% | 核心算法 |

---

## 6. 本地调试技巧

### 后端调试

**1. 使用 Uvicorn 热重载**
```bash
# --reload 会自动检测代码变更并重启
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**2. 设置 DEBUG 日志级别**
```bash
# 在 .env 中设置
LOG_LEVEL=DEBUG

# 或通过环境变量启动
LOG_LEVEL=DEBUG uvicorn main:app --reload --port 8000
```

**3. 使用 Python Debugger**
```python
# 在代码中插入断点
import pdb; pdb.set_trace()

# 或使用 breakpoint() (Python 3.7+)
breakpoint()
```

**4. VS Code 调试配置 (.vscode/launch.json)**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload", "--port", "8000"],
      "cwd": "${workspaceFolder}/scripts",
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
```

**5. API 调试技巧**
```bash
# 使用 httpie (更友好的 curl 替代)
pip install httpie
http POST http://localhost:8000/api/v1/content/generate topic="AI" platform="抖音"

# 查看 LLM 原始响应（设置 LOG_LEVEL=DEBUG）
LOG_LEVEL=DEBUG uvicorn main:app --port 8000

# 测试 SSE 流式
curl -N -X POST http://localhost:8000/api/v1/stream/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"AI工具","platform":"抖音","persona":"学长型","duration":60}'
```

### 前端调试

```bash
# 开发模式启动
cd saas && pnpm dev

# 查看 Next.js 日志
# 页面 F12 → Console/Network 面板

# 前端 API 代理调试
# 访问 /api/* 会代理到后端 :8000
# 可在浏览器 Network 面板查看请求和响应
```

### 常见调试场景

**场景 1: LLM 返回格式错误**
```bash
# 1. 设置日志级别为 DEBUG
LOG_LEVEL=DEBUG

# 2. 直接测试 LLM API
python -c "
import asyncio
from services.deepseek import DeepSeekClient
c = DeepSeekClient()
r = asyncio.run(c.chat('你好'))
print(r)
"
```

**场景 2: 缓存问题**
```bash
# 查看缓存内容
python -c "
import asyncio
from services.cache import CacheService
c = CacheService()
r = asyncio.run(c.get('cache_key_here'))
print(r)
"

# 清除所有缓存
python -c "
import asyncio
from services.cache import _default_cache
asyncio.run(_default_cache.close())
"
```

**场景 3: Fire Score 校准调试**
```bash
# 直接查看 SQLite 数据库
python -c "
import sqlite3
conn = sqlite3.connect('output/tracker.db')
conn.row_factory = sqlite3.Row
rows = conn.execute('SELECT * FROM performance_records LIMIT 5').fetchall()
for r in rows:
    print(dict(r))
"
```

**场景 4: 测试路由策略**
```python
# scripts/debug_router.py
import asyncio
from services.router import default_router, TaskType

async def debug():
    # 测试模型推荐
    model = default_router.select_model(TaskType.CONTENT_GENERATION, "balanced")
    print(f"推荐模型: {model}")

    # 测试成本估算
    cost = default_router.estimate_cost("你好，请介绍一下人工智能", "deepseek")
    print(f"估算成本: {cost} 元")

    # 查看历史统计
    stats = default_router.get_stats()
    print(f"路由统计: {stats}")

asyncio.run(debug())
```

### Docker 调试

```bash
# 查看容器日志
docker compose logs -f api      # 后端日志
docker compose logs -f saas     # 前端日志
docker compose logs -f redis    # Redis 日志

# 进入容器内部调试
docker compose exec api bash
docker compose exec saas sh

# 查看数据库
docker compose exec postgres psql -U zhimeiquan zhimeiquan

# 查看 Docker 资源
docker stats

# 重建特定服务
docker compose build api
docker compose up -d api
```
