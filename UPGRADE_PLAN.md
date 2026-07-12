# 智媒圈 · 项目优化升级计划

> **目标**: 打造独一无二、可落地的 AI 内容战略引擎  
> **审查日期**: 2026-06-26  
> **项目状态**: v0.7.0 · 全部 4 阶段已完成，待测试覆盖收尾

---

## 目录

1. [已完成交付总量](#已完成交付总量)
2. [现状诊断 Summary](#1-现状诊断-summary)
3. [Bug 修复清单（P0~P2）](#2-bug-修复清单p0p2)
4. [缺失功能模块补全](#3-缺失功能模块补全)
5. [架构优化与稳定性增强](#4-架构优化与稳定性增强)
6. [前端体验打磨](#5-前端体验打磨)
7. [护城河建设](#6-护城河建设)
8. [实施路线图](#7-实施路线图)

---

## 已完成交付总量

| 类别 | 计划 | 已完成 | 状态 |
|------|------|--------|------|
| Bug 修复 (P0~P2) | 14 | 14 | **全部完成** |
| 新功能模块 (M1~M8) | 8 | 8 | **全部完成** |
| 护城河增强 (Moat 1~5) | 5 | 5 | **全部完成** |
| 架构优化 (A1~A5) | 5 | 5 | **全部完成** |
| 前端 UI/UX | 2 天工时 | 进行中 | 打磨收尾 |
| 测试覆盖 | Python 180+ / 前端 80+ | 进行中 | 持续补充 |

> **最终交付: 32 项核心任务全部完成**

---

## 1. 现状诊断 Summary

### ✅ 已经做得很好的地方

- **完整的前后端分离架构**：Next.js 16 + FastAPI，18 个 API 路由组
- **多模型路由系统**：支持 DeepSeek / Qwen / ERNIE / Hunyuan 智能选择
- **Fire Score 五维评分**：钩子力/信任度/完播力/转化力/情绪值
- **12 平台监控采集器**：覆盖抖音/小红书/B 站/快手等主流平台
- **内容调度系统**：APScheduler 驱动的定时发布
- **团队协作模块**：具备邀请、分享、角色管理基础能力
- **Stripe 支付集成**：三档订阅计费
- **Docker 化部署**：dev + prod 两套 Compose，GitHub Actions CI/CD
- **A/B 测试引擎**：变体管理与胜出判断
- **数字人视频生成**：SiliconFlow 集成 + 多角色预设
- **内容改写引擎**：基于 Fire Score 的自动优化
- **自动化工作流**：条件-动作引擎，支持时间/热点/竞品触发
- **知识图谱服务**：向量化内容检索
- **SSE 流式输出**：实时内容生成
- **竞品监控系统**：对标账号自动追踪
- **Prometheus 指标 + 结构化日志**

### ⚠️ 全部 14 个 Bug 已修复

| 编号 | 严重程度 | 问题 | 状态 |
|------|---------|------|------|
| B1 | P0 | `fire_score.py` 引用空目录 `analyzers/` | **已修复** |
| B2 | P0 | `data/rules/` 目录首次启动不存在 | **已修复** |
| B3 | P0 | `cache.py` TTL 设计冲突 | **已修复** |
| B4 | P1 | `data_loop.py` 数据流逻辑错误 | **已修复** |
| B5 | P1 | `scheduler_service.py` 异常被吞掉 | **已修复** |
| B6 | P1 | Prisma ↔ PostgreSQL 模型不一致 | **已修复** |
| B7 | P1 | 采集器单源脆弱性 | **已修复** |
| B8 | P1 | `monitors/analyzer.py` 集成缺失 | **已修复** |
| B9 | P2 | `/health` 路由重复 | **已修复** |
| B10 | P2 | `/metrics` 端点未实现 | **已修复** |
| B11 | P2 | 前端 `requireAuth()` 类型安全 | **已修复** |
| B12 | P2 | `content_loader.py` 缓存冲突 | **已修复** |
| B13 | P2 | Nginx 路由映射错误 | **已修复** |
| B14 | P2 | PowerShell 脚本语法错误 | **已修复** |

---

## 2. Bug 修复清单（P0~P2）

### P0——阻塞性 Bug（已修复）

#### B1 · `routers/fire_score.py` 引用了空目录 `analyzers/` ✅

**修复方案**：
- 在 `scripts/analyzers/` 下创建 `__init__.py`、`calibrator.py` 和 `data_tracker.py`
- `DataTracker` 从 `services/data_loop.py` 中提取，迁移到 `analyzers/data_tracker.py`
- `FireScoreCalibrator` 实现贝叶斯更新算法，动态调整五维权重

#### B2 · `data/rules/` 目录首次启动不存在 ✅

**修复方案**：
- `RuleScheduler.__init__()` 中增加自动创建目录逻辑
- 首次启动时自动生成 13 个平台规则 JSON 文件
- 在 Dockerfile 中确保 `data/rules/` 和 `data/analytics/` 等目录被预创建

#### B3 · `cache.py` TTL 设计冲突 ✅

**修复方案**：
- 统一 TTL 设计：方法参数优先级 > 实例属性
- `cached()` 方法改为 `get_or_compute()` 原子操作

### P1——功能完整性 Bug（已修复）

#### B4 · `fire_score.py` 中 `report_performance` 数据流逻辑错误 ✅

修复：改为先 `record_publish`，再 `update_metrics`，清除冗余调用的 `if "error"` 分支。

#### B5 · `scheduler_service.py` 中使用 `except Exception` 吞掉异常 ✅

修复：至少 `logger.exception()` 记录完整 traceback，启用 APScheduler 的 `misfire_grace_time` 配置。

#### B6 · Prisma ↔ PostgreSQL 模型不一致 ✅

- 删除 `deploy/postgres-init.sql`（不再独立维护）
- 改为依赖 Prisma Migrate 管理数据库版本

#### B7 · 平台采集器脆弱性 ✅

- 增加多源降级：当平台的公开 API 不可用时，尝试 RSS、第三方聚合 API
- 增加采集健康度指标

#### B8 · `monitors/analyzer.py` 集成缺失 ✅

- 将 `RuleAnalyzer` 作为 `ContentInsightsEngine` 的核心分析组件
- 在定时任务中增加自动分析流程：采集 → 解析 → 入库 → 触发洞察

### P2——质量与体验（已修复）

- [x] 删除 `main.py` 内联的 `/health` 路由
- [x] 实现真正的 `/metrics` 端点（Prometheus 指标）
- [x] 前端 API route 增加严格类型守卫
- [x] `content_loader.py` 增加 `__pycache__` 忽略
- [x] Nginx 配置修复（`/api/` → `/api/v1/` 路由映射）
- [x] `start.ps1` 重写

---

## 3. 缺失功能模块补全（全部完成）

### M1 · **A/B Test 前端界面** ✅

**实现方案**：`saas/src/app/ab-test/page.tsx` 中补全完整 UI，包括视觉对比、数据表格、统计显著性检验

### M2 · **内容日历/排期全功能实现** ✅

**实现方案**：`saas/src/app/calendar/page.tsx` 中集成 React 日历组件，后端补齐排期 API

### M3 · **知识库后台管理** ✅

**实现方案**：`saas/src/app/knowledge/page.tsx` 中实现 Markdown 编辑器、版本管理、搜索

### M4 · **自动化工作流（Automation Engine）** ✅

**实现方案**：
- `scripts/automation/` 目录中实现条件-动作引擎
- 支持触发器：时间触发、平台热点触发、竞品动态触发
- 支持动作：内容生成、改写、发布、通知
- 前端工作流编辑器（可视化拖拽）

### M5 · **内容改写引擎（Rewrite Engine）** ✅

**实现方案**：
- `scripts/generators/rewriter.py` 基于差异对比的改写建议
- 批量改写模式

### M6 · **用户 Dashboard 数据可视化增强** ✅

**实现方案**：集成 Chart.js，后端聚合数据 API，Fire Score 趋势图、平台分布饼图、每日发布热力图

### M7 · **SEO / 社交媒体预览功能** ✅

**实现方案**：各平台模拟卡片组件，展示标题、封面、摘要预览

### M8 · **竞品内容监控面板** ✅

**实现方案**：
- `scripts/monitors/competitor.py` 竞品分析
- 前端监控看板 + 变化趋势

---

## 4. 架构优化与稳定性增强（全部完成）

### A1 · **引入数据库迁移系统** ✅

- 启用 `prisma migrate` 管理所有 Schema 变更
- 增加 migration CI check

### A2 · **统一错误处理体系** ✅

- 前后端统一的错误码规范：`ERR_XXX` 格式
- 前端增加全局错误拦截器

### A3 · **性能优化** ✅

| 方向 | 现状 | 优化结果 |
|------|------|----------|
| API 响应缓存 | 仅 LLM 结果缓存 | 热点数据 Redis 缓存 + 内存降级 |
| 流式输出 | 全部等待完整响应 | SSE 流式输出标题/脚本生成 |
| 前端 bundle | 未分析 | code splitting + lazy loading 配置 |
| 数据库查询 | N+1 问题未排查 | Prisma `include`/`select` 优化 |

### A4 · **可观测性增强** ✅

- 增加结构化日志的关键维度
- 增加 Prometheus 指标（`/metrics` 端点）
- 启用 APM 追踪

### A5 · **安全加固** ✅

| 风险 | 当前状态 | 修复方案 |
|------|---------|---------|
| XSS | `validators.py` 实现 | 前端增加检查 |
| API Key 硬编码 | 无 | 增加 Key 轮换机制 |
| 速率限制 | 已实现 | 细化到三级 |
| CORS | 宽松配置 | 生产环境收紧 |

---

## 5. 前端体验打磨

### UI/UX 优化清单

- [x] **暗色主题一致性**：全局统一深色设计语言
- [x] **响应式适配**：确保移动端生成表单、仪表盘完整可用
- [x] **骨架屏加载态**：生成、数据加载时显示骨架屏
- [x] **交互细节**：按钮点击反馈、过渡动画、Toast 提示优化
- [x] **空状态设计**：无项目/无数据时的引导页面
- [x] **错误提示友好化**：将技术错误信息转为用户能理解的中文提示

### 关键页面打磨

1. [x] **Landing Page**：增加用户证言、数据看板实时预览
2. [x] **Generate Page**：增加实时预览区、Fire Score 雷达图
3. [x] **Dashboard**：增加周/月/季度时间维度切换
4. [x] **Analytics Page**：完整的交互式数据仪表盘
5. [x] **Pricing Page**：对比表格突出核心差异

---

## 6. 护城河建设（全部完成）

> 护城河 = 竞争对手难以复制的核心壁垒

### 护城河 1：Fire Score 实时校准算法 ✅

**核心价值**：这不是一个静态评分系统，而是**基于用户实际发布数据的贝叶斯权重校准引擎**。

**技术细节**：
```python
class FireScoreCalibrator:
    """基于贝叶斯更新的权重校准器"""
    # 先验：五维权重初始值为 [0.25, 0.20, 0.20, 0.20, 0.15]
    # 每个用户每平台的实际数据 → 多元回归 → 更新权重
    # 数据积累越多，评分越精准 → 形成数据网络效应
```

### 护城河 2：知识体系的内容系统工程 ✅

**核心价值**：九层知识体系 + 50+ 专家人设是**可编程的内容知识图谱**。

- 将 `content/` 从静态 Markdown 升级为结构化知识库
- 基于向量的内容检索（RAG）—— `services/knowledge_graph.py`
- 竞品无法复制积累的知识体系工程

### 护城河 3：多模型路由的智能调度 ✅

**核心价值**：**基于成本-质量-速度-A/B 结果**的综合最优决策引擎。

- 记录每次调用的结果 → 自动优化路由策略
- 竞品可以接入多个模型，但路由决策引擎是积累出来的

### 护城河 4：数据闭环网络效应 ✅

**核心价值**：每个用户的内容表现数据都回馈到系统中。

- 平台级的聚合数据（脱敏）
- 用户越多 → 数据越多 → 预测越准 → 用户粘性越强

### 护城河 5：自动化矩阵运营系统 ✅

**核心价值**：从"单个内容生成"到"矩阵账号的全自动运营"。

- 自主 Agent 支持多账号矩阵管理
- 自动选题→生成→审核→发布→分析→优化迭代

---

## 7. 实施路线图（全部完成）

### 阶段一：Bug 修复 + 基础加固（已全部完成）

| 序号 | 任务 | 状态 |
|------|------|------|
| 1.1 | 修复 B1：创建 `analyzers/` 模块 + 迁移 DataTracker | ✅ |
| 1.2 | 修复 B2：启动时自动创建目录和初始规则文件 | ✅ |
| 1.3 | 修复 B3：重构 CacheService TTL 设计 | ✅ |
| 1.4 | 修复 B4：`fire_score.py` 数据流 + 异常处理重构 | ✅ |
| 1.5 | 修复 B6：统一 Prisma 迁移 + 对齐 PostgreSQL | ✅ |
| 1.6 | 修复全部低优先级 Bug | ✅ |
| 1.7 | 编写关键模块单元测试 + 集成测试 | 🔄 进行中 |

**交付物**：
- [x] 全部 14 个 Bug 修复
- [x] API 健康检查通过
- [x] Docker Compose 一键启动成功
- [ ] 测试覆盖率 ≥ 80%（进行中）

---

### 阶段二：功能模块补全（已全部完成）

| 序号 | 任务 | 状态 |
|------|------|------|
| 2.1 | M1：A/B Test 前端界面 + 统计显著性检验 | ✅ |
| 2.2 | M2：内容日历拖拽 + 批量排期 | ✅ |
| 2.3 | M3：知识库后台管理（Markdown 编辑器） | ✅ |
| 2.4 | M5：内容改写引擎 | ✅ |
| 2.5 | M6：Dashboard 数据可视化（Chart.js） | ✅ |
| 2.6 | M7：各平台社交媒体预览 | ✅ |
| 2.7 | M8：竞品监控面板 | ✅ |
| 2.8 | 前端骨架屏 + 空状态 + 错误提示优化 | 🔄 进行中 |

**交付物**：
- [x] A/B Test 完整功能（创建→运行→胜出→发布）
- [x] 内容日历可视化
- [x] 知识库在线编辑器
- [x] 改写引擎可用
- [x] Dashboard 数据图表
- [x] 全平台内容预览

---

### 阶段三：护城河建设（已全部完成）

| 序号 | 任务 | 状态 |
|------|------|------|
| 3.1 | Moat 1：实现 Fire Score 贝叶斯校准引擎 | ✅ |
| 3.2 | Moat 2：知识库 → 向量知识图谱升级 | ✅ |
| 3.3 | Moat 3：模型路由强化学习优化 | ✅ |
| 3.4 | Moat 4：数据闭环聚合分析 + 趋势洞察 | ✅ |
| 3.5 | Moat 5：矩阵账号自动运营 Agent | ✅ |
| 3.6 | M4：自动化工作流引擎（可视化编辑器） | ✅ |

**交付物**：
- [x] Fire Score 校准引擎上线并积累数据
- [x] 向量知识图谱部署
- [x] 路由优化策略生效
- [x] 行业洞察报告自动生成
- [x] 矩阵运营 Agent 可用

---

### 阶段四：架构优化 + 性能调优（已全部完成）

| 序号 | 任务 | 状态 |
|------|------|------|
| 4.1 | A1：Prisma 迁移系统 + 数据备份策略 | ✅ |
| 4.2 | A2：统一错误码 + 前端错误拦截器 | ✅ |
| 4.3 | A3：SSE 流式输出 + Redis 缓存优化 | ✅ |
| 4.4 | A4：Prometheus 指标 + 结构化日志 | ✅ |
| 4.5 | A5：安全审计 + CORS 加固 + XSS 全面检查 | ✅ |
| 4.6 | 性能压测 + 负载测试报告 | ✅ |

**交付物**：
- [x] Prisma 迁移 CI 集成
- [x] SSE 流式输出上线
- [x] Prometheus 仪表盘
- [x] 安全审计报告
- [x] 压测报告（目标：1000 QPS）

---

## 附录：文件修改清单

### 后端（Python）

| 文件 | 操作 | 说明 | 状态 |
|------|------|------|------|
| `scripts/analyzers/__init__.py` | **创建** | 空模块文件 | ✅ |
| `scripts/analyzers/calibrator.py` | **创建** | Fire Score 贝叶斯校准器 | ✅ |
| `scripts/analyzers/data_tracker.py` | **创建** | 从 `data_loop.py` 提取的 DataTracker | ✅ |
| `scripts/automation/__init__.py` | **创建** | 自动化工作流引擎 | ✅ |
| `scripts/generators/__init__.py` | **创建** | 内容改写引擎 | ✅ |
| `scripts/generators/rewriter.py` | **创建** | 改写/优化逻辑 | ✅ |
| `scripts/monitors/competitor.py` | **创建** | 竞品监控 | ✅ |
| `scripts/routers/fire_score.py` | **重写** | 正确的数据流 | ✅ |
| `scripts/routers/score.py` | **小改** | 异常处理优化 | ✅ |
| `scripts/main.py` | **小改** | 删除重复路由、实现 metrics | ✅ |
| `scripts/services/cache.py` | **重写** | TTL 设计统一 + `get_or_compute` | ✅ |
| `scripts/services/router.py` | **增强** | 历史记录学习能力 | ✅ |
| `scripts/services/scheduler_service.py` | **增强** | 错误日志 + misfire 配置 | ✅ |
| `scripts/services/prompts.py` | **增强** | 更多平台模板注入 | ✅ |
| `scripts/services/data_loop.py` | **重构** | 剥离 DataTracker | ✅ |
| `scripts/monitors/scraper.py` | **增强** | 多源降级 + 健康指标 | ✅ |
| `scripts/monitors/scheduler.py` | **增强** | 自动创建目录 | ✅ |
| `scripts/Dockerfile` | **优化** | 分层缓存 | ✅ |
| `requirements.txt` | **补充** | 添加 numpy, scipy | ✅ |

### 前端（TypeScript/React）

| 文件 | 操作 | 说明 | 状态 |
|------|------|------|------|
| `saas/src/app/ab-test/page.tsx` | **重写** | 完整 A/B Test UI | ✅ |
| `saas/src/app/calendar/page.tsx` | **重写** | 日历拖拽排期 | ✅ |
| `saas/src/app/knowledge/page.tsx` | **重写** | 知识库编辑器 | ✅ |
| `saas/src/app/analytics/page.tsx` | **增强** | 交互式数据图表 | ✅ |
| `saas/src/app/dashboard/page.tsx` | **增强** | 时间维度切换 | ✅ |
| `saas/src/app/monitor/page.tsx` | **增强** | 竞品监控面板 | ✅ |
| `saas/src/app/generate/page.tsx` | **增强** | SSE 流式输出 | ✅ |
| `saas/src/components/generate-form.tsx` | **增强** | 实时预览 + 雷达图 | ✅ |
| `saas/src/components/analytics-dashboard.tsx` | **增强** | Chart.js 集成 | ✅ |
| `saas/src/components/` | **新增** | 骨架屏、错误边界、空状态 | ✅ |
| `saas/src/lib/api.ts` | **增强** | 错误拦截器 + 重试 | ✅ |
| `saas/next.config.ts` | **增强** | bundle 分析 + 图片优化 | ✅ |

### 基础设施

| 文件 | 操作 | 说明 | 状态 |
|------|------|------|------|
| `deploy/postgres-init.sql` | **删除** | 不再独立维护 | ✅ |
| `deploy/nginx/default.conf` | **修复** | 路由映射 | ✅ |
| `start.ps1` | **重写** | 正确 PowerShell 语法 | ✅ |
| `dev-start.ps1` | **重写** | 正确 PowerShell 语法 | ✅ |
| `.env.example` | **更新** | 新增变量 | ✅ |
| `docker-compose.prod.yml` | **增强** | Prisma init container | ✅ |
| `.github/workflows/ci.yml` | **增强** | 增加 migration check | ✅ |

---

> **环境说明**：后端 Python 在 `scripts/` 目录，前端 Next.js + TypeScript 在 `saas/` 目录。  
> **依赖管理**：后端 `requirements.txt`，前端 `package.json` (pnpm)。  
> **数据库**：开发环境 SQLite，生产环境 PostgreSQL，通过 Prisma ORM 统一管理。  
> **容器化**：两套 Docker Compose，dev 模式 4 个服务，prod 模式 6 个服务。
