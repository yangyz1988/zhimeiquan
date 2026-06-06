# 智媒圈全面升级计划

> 项目状态：骨架搭好，肉还没长。需要从 mock 走向真实实现。

---

## Phase 1: AI 引擎接入 (核心)

### 1.1 DeepSeek API 客户端

```
scripts/services/
├── __init__.py
├── deepseek.py          # DeepSeek API 封装
├── prompts.py           # Prompt 模板
└── models.py            # 请求/响应模型
```

**任务：**
- [ ] 创建 DeepSeek 异步客户端 (httpx)
- [ ] 定义 Prompt 模板：口播稿生成、标题生成、Fire Score 评分
- [ ] 实现流式输出支持
- [ ] 添加重试和错误处理

### 1.2 口播稿生成器

**Prompt 设计：**
```
你是一个专业的自媒体口播稿创作者。
平台：{platform}
主题：{topic}
人设：{persona}
时长：{duration}秒

请生成：
1. 标题（5个备选）
2. 口播稿正文
3. 字幕时间轴
4. 标签
```

### 1.3 Fire Score 智能评分

**五维评分 Prompt：**
```
请对以下内容进行五维度评分（0-100）：
- 钩子力：前3秒能否让人停住
- 信任度：内容是否可信、有依据
- 完播力：节奏是否紧凑、不无聊
- 转化力：用户看完会不会关注/收藏
- 情绪值：有没有情绪共鸣

标题：{title}
正文：{body}
平台：{platform}

输出 JSON 格式...
```

---

## Phase 2: 前端 UI 完善

### 2.1 安装 shadcn/ui

```bash
cd saas
npx shadcn@latest init
npx shadcn@latest add button card input textarea select badge dialog tabs
```

### 2.2 页面结构

```
saas/src/app/
├── layout.tsx              # 根布局 (providers, header)
├── page.tsx                # Landing page
├── globals.css             # Tailwind + 主题变量
├── dashboard/
│   ├── page.tsx            # 工作台
│   └── layout.tsx          # 侧边栏布局
├── generate/
│   └── page.tsx            # 内容生成页
├── projects/
│   ├── page.tsx            # 项目列表
│   └── [id]/page.tsx       # 项目详情
└── api/
    └── content/
        └── route.ts        # Next.js API route (代理)
```

### 2.3 核心组件

```
saas/src/components/
├── ui/                     # shadcn 组件
├── header.tsx              # 顶部导航
├── sidebar.tsx             # 侧边栏
├── generate-form.tsx       # 内容生成表单
├── fire-score-chart.tsx    # 五维评分雷达图
├── content-preview.tsx     # 内容预览
├── platform-badge.tsx      # 平台标签
└── providers.tsx           # Theme + Query providers
```

### 2.4 Landing Page 设计

- Hero section: 标题 + 副标题 + CTA
- 特性展示: 6 大 AI 引擎
- 评分演示: Fire Score 交互式展示
- 平台覆盖: 13 平台 logo 展示
- 定价方案: 三档定价

---

## Phase 3: 后端 API 完善

### 3.1 路由重构

```
scripts/routers/
├── content.py              # POST /generate, GET /list, GET /{id}
├── titles.py               # POST /generate
├── score.py                # POST /score
├── projects.py             # CRUD 项目管理
└── health.py               # GET /health, GET /metrics
```

### 3.2 数据库集成

- [ ] Prisma Client 调用 (通过 HTTP 或直接 Python SQLite)
- [ ] 项目 CRUD 操作
- [ ] 生成结果持久化
- [ ] 使用记录统计

### 3.3 Redis 缓存

- [ ] 热门主题缓存
- [ ] 生成结果缓存 (避免重复调用)
- [ ] 限流计数器

---

## Phase 4: 认证系统

### 4.1 方案选型

| 方案 | 优点 | 缺点 |
|:-----|:-----|:-----|
| **Clerk** | 最快集成、美观 UI | 付费、数据在外部 |
| **NextAuth.js** | 免费、灵活 | 需要更多配置 |
| **Supabase Auth** | 免费额度大 | 依赖 Supabase |

**推荐：Clerk** (快速出成品)

### 4.2 实现

```bash
npx shadcn@latest add auth
# 集成 Clerk
```

---

## Phase 5: 测试

### 5.1 后端测试

```
scripts/tests/
├── test_content.py
├── test_titles.py
├── test_score.py
└── conftest.py
```

### 5.2 前端测试

```
saas/src/__tests__/
├── generate-form.test.tsx
├── fire-score-chart.test.tsx
└── api.test.ts
```

---

## Phase 6: 部署优化

### 6.1 Docker 优化

- [ ] 多阶段构建优化
- [ ] 健康检查配置
- [ ] 日志收集

### 6.2 CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to server
        run: ...
```

---

## 执行顺序

```
Phase 1 (AI引擎) ──→ Phase 3 (后端API) ──→ Phase 5 (测试)
                    ↓
Phase 2 (前端UI) ──→ Phase 4 (认证) ──→ Phase 6 (部署)
```

**并行执行：** Phase 1 和 Phase 2 可同时进行

---

## 优先级

| 优先级 | 内容 | 预计耗时 |
|:-------|:-----|:---------|
| P0 | DeepSeek API 接入 | 2h |
| P0 | 生成表单 + 结果展示 | 3h |
| P1 | 项目管理 CRUD | 2h |
| P1 | Landing Page | 2h |
| P2 | 认证系统 | 2h |
| P2 | 测试 | 2h |
| P3 | 部署优化 | 1h |

**总计：约 14 小时**
