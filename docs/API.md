# 智媒圈 API 参考手册

> 版本: 0.7.0 | 基础 URL: `http://localhost:8000` | 生产 URL: `https://api.zhimeiquan.com`

---

## 目录

1. [概述](#1-概述)
2. [认证与鉴权](#2-认证与鉴权)
3. [错误码体系](#3-错误码体系)
4. [路由总览](#4-路由总览)
5. [组 1: 健康检查](#5-组-1-健康检查)
6. [组 2: 内容生成](#6-组-2-内容生成)
7. [组 3: 标题生成](#7-组-3-标题生成)
8. [组 4: 内容评分](#8-组-4-内容评分)
9. [组 5: Fire Score 校准](#9-组-5-fire-score-校准)
10. [组 6: 爆款监控/规则](#10-组-6-爆款监控规则)
11. [组 7: 视频生成](#11-组-7-视频生成)
12. [组 8: 数据闭环](#12-组-8-数据闭环)
13. [组 9: A/B 测试](#13-组-9-ab-测试)
14. [组 10: 内容调度](#14-组-10-内容调度)
15. [组 11: 图像生成](#15-组-11-图像生成)
16. [组 12: 模板系统](#16-组-12-模板系统)
17. [组 13: 自主 Agent](#17-组-13-自主-agent)
18. [组 14: 团队协作](#18-组-14-团队协作)
19. [组 15: 模型路由](#19-组-15-模型路由)
20. [组 16: 内容洞察](#20-组-16-内容洞察)
21. [组 17: 竞品监控](#21-组-17-竞品监控)
22. [组 18: SSE 流式生成](#22-组-18-sse-流式生成)

---

## 1. 概述

智媒圈 API 提供一站式 AI 内容生产与分发服务，涵盖内容生成、评分优化、多平台分发、数据分析和自动化运营。

### 基础信息

| 项目 | 值 |
|------|-----|
| 框架 | FastAPI 0.115+ |
| 文档地址 | `http://localhost:8000/docs` (Swagger UI) |
| 备用文档 | `http://localhost:8000/redoc` (ReDoc) |
| 协议 | HTTP/REST |
| 数据格式 | JSON (UTF-8) |
| SSE 格式 | `text/event-stream` |

### API 规范

- 所有请求和响应体均为 JSON 格式
- 日期时间使用 ISO 8601 格式: `2026-06-26T10:00:00+08:00`
- 分页参数: `page` (从 1 开始)、`page_size` (默认 20，最大 100)
- 响应中的 `detail` 字段包含错误描述
- 所有长文本字段限制最大 10000 字符

---

## 2. 认证与鉴权

API 使用 X-API-Key 头部进行鉴权（可选，由 `API_SECRET` 环境变量控制）。

### 请求头格式

```
X-API-Key: your-api-secret-here
```

### 免认证端点

以下端点不需要 API Key:
- `/health`
- `/ready`
- `/metrics`
- `/docs` (Swagger UI)
- `/openapi.json`
- OPTIONS 请求

### 前端认证

前端使用 Clerk 进行用户认证，流程如下:
1. 用户在 Clerk 登录/注册
2. 前端通过 Next.js API Route (`/api/*`) 代理后端请求
3. 后端通过 `API_SECRET` 验证前端来源

### Stripe Webhook 签名验证

支付 Webhook 使用 Stripe 签名验证（`stripe-signature` 头部），无需 X-API-Key。

---

## 3. 错误码体系

所有 API 错误返回统一格式:

```json
{
  "detail": "人类可读的错误描述",
  "code": "ERR_XXX"
}
```

### 错误码表

| 错误码 | HTTP 状态 | 描述 |
|--------|----------|------|
| AUTH001 | 401 | 未登录 |
| AUTH002 | 403 | API 密钥无效 |
| AUTH003 | 403 | 权限不足 |
| CONT001 | 500 | 内容生成失败 |
| CONT002 | 500 | AI 返回格式错误 |
| CONT003 | 400 | 主题不能为空 |
| CONT004 | 400 | 平台不支持 |
| RATE001 | 429 | 请求过于频繁 |
| SERV001 | 503 | 服务暂时不可用 |
| SERV002 | 503 | API 服务未启动 |
| DATA001 | 404 | 记录不存在 |
| DATA002 | 422 | 数据验证失败 |

### 通用错误响应

```json
// 400 参数验证失败
{
  "detail": "参数验证失败",
  "errors": [
    {
      "type": "string_too_short",
      "loc": ["body", "topic"],
      "msg": "field required",
      "input": null
    }
  ]
}

// 429 限流
{
  "detail": "请求过于频繁"
}

// 500 服务端错误
{
  "detail": "内容生成失败，请稍后重试"
}

// 503 服务不可用
{
  "detail": "服务暂时不可用",
  "code": "SERV001"
}
```

---

## 4. 路由总览

共 18 组路由 + 2 个独立端点，覆盖 50+ 个 API 端点:

| # | 前缀 | 标签 | 端点数量 |
|---|------|------|:--------:|
| 1 | `/health`, `/ready` | 健康检查 | 2 |
| 2 | `/api/v1/content` | 内容生成 | 2 |
| 3 | `/api/v1/titles` | 标题生成 | 1 |
| 4 | `/api/v1/content` | 内容评分 | 1 |
| 5 | `/api/v1/fire-score` | Fire Score 校准 | 3 |
| 6 | `/api/v1/monitor` | 爆款监控/规则 | 4 |
| 7 | `/api/v1/video` | 视频生成 | 4 |
| 8 | `/api/v1/analytics` | 数据闭环 | 5 |
| 9 | `/api/v1/ab-test` | A/B 测试 | 4 |
| 10 | `/api/v1/calendar` | 内容调度 | 5 |
| 11 | `/api/v1/image` | 图像生成 | 2 |
| 12 | `/api/v1/templates` | 模板系统 | 4 |
| 13 | `/api/v1/agent` | 自主 Agent | 3 |
| 14 | `/api/v1/team` | 团队协作 | 5 |
| 15 | `/api/v1/router` | 模型路由 | 6 |
| 16 | `/api/v1/insights` | 内容洞察 | 4 |
| 17 | `/api/v1/competitors` | 竞品监控 | 6 |
| 18 | `/api/v1/stream` | SSE 流式生成 | 1 |
| - | `/metrics` | Prometheus 指标 | 1 |
| - | `/api/v1/knowledge` | 知识库 | 3 |

---

## 5. 组 1: 健康检查

### 5.1 GET /health — 存活检查

Liveness probe，用于 Kubernetes/Docker 健康检查。

**请求示例:**
```bash
curl -s http://localhost:8000/health | python -m json.tool
```

**响应:**
```json
{
  "status": "ok",
  "timestamp": "2026-06-26T10:00:00",
  "version": "0.5.0"
}
```

### 5.2 GET /ready — 就绪检查

Readiness probe，检查所有外部依赖是否就绪。

**请求示例:**
```bash
curl -s http://localhost:8000/ready | python -m json.tool
```

**响应 (全部正常):**
```json
{
  "status": "ready",
  "checks": {
    "api": true,
    "redis": true,
    "deepseek": true
  },
  "timestamp": "2026-06-26T10:00:00"
}
```

**响应 (Redis 不可用，仍返回 ready):**
```json
{
  "status": "ready",
  "checks": {
    "api": true,
    "redis": false,
    "deepseek": true
  },
  "timestamp": "2026-06-26T10:00:00"
}
```

> 注意: 当 `api` 检查失败时（极少发生），`status` 为 `not_ready`。

---

## 6. 组 2: 内容生成

### 6.1 POST /api/v1/content/generate — 生成口播内容

根据主题、平台和人设生成完整的口播脚本，包含标题、字幕、标签等。

**请求体:**
```json
{
  "topic": "如何用 AI 工具提升工作效率",
  "platform": "抖音",
  "persona": "学长型",
  "duration": 60
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| topic | string | 是 | - | 内容主题，1-200 字符 |
| platform | string | 否 | "抖音" | 目标平台，见[平台列表](#平台列表) |
| persona | string | 否 | "学长型" | 人设风格 |
| duration | int | 否 | 60 | 目标时长(秒)，5-3600 |

**响应:**
```json
{
  "titles": [
    "打工人的效率翻倍秘诀，AI 工具实测推荐",
    "3 款 AI 工具让我准时下班，第 2 个太实用"
  ],
  "script": "[开场]你是不是也经常加班到深夜？...\n[正文]今天给大家推荐 3 个超实用的 AI 工具...\n[结尾]关注我，下期分享更多效率秘籍！",
  "subtitles": [
    {"time": "00:00", "text": "你是不是也经常加班到深夜？"},
    {"time": "00:05", "text": "今天给大家推荐 3 个超实用的 AI 工具"}
  ],
  "tags": ["AI工具", "效率提升", "职场技能"],
  "hook": "你是不是也经常加班到深夜？",
  "call_to_action": "关注我，下期分享更多效率秘籍！"
}
```

**curl 示例:**
```bash
curl -s -X POST http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-secret" \
  -d '{"topic":"如何用AI工具提升工作效率","platform":"抖音","persona":"学长型","duration":60}' \
  | python -m json.tool
```

**限流:** 每平台每分钟 30 次请求

### 6.2 POST /api/v1/content/rewrite — 内容改写

使用改写引擎优化内容，目标 Fire Score 95+（最多 3 轮迭代）。

**请求体:**
```json
{
  "content": {
    "title": "AI 工具推荐",
    "body": "今天给大家推荐一些 AI 工具...",
    "hook": "这些 AI 工具你一定要知道",
    "tags": ["AI"],
    "call_to_action": "点赞收藏"
  },
  "platform": "抖音",
  "target_score": 95,
  "max_iterations": 3
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | object | 是 | 待改写的内容 |
| content.title | string | 是 | 标题 |
| content.body | string | 是 | 正文/脚本 |
| content.hook | string | 否 | 钩子文案 |
| content.tags | array | 否 | 标签列表 |
| content.call_to_action | string | 否 | 引导语 |
| platform | string | 是 | 目标平台 |
| target_score | int | 否 | 目标分数 (默认 95) |
| max_iterations | int | 否 | 最大迭代次数 (默认 3) |

**响应:**
```json
{
  "content_id": "rewrite_1719360000",
  "original": { "...": "..." },
  "rewritten": { "...": "..." },
  "original_score": { "total": 68, "level": "Lv4 普爆", "hook": 65, "trust": 70, "retention": 68, "conversion": 60, "emotion": 72, "suggestions": [...], "analysis": "..." },
  "new_score": { "total": 96, "level": "Lv1 必爆", "hook": 95, "trust": 92, "retention": 94, "conversion": 90, "emotion": 92, "suggestions": [...], "analysis": "..." },
  "improved": true,
  "iterations": 2,
  "changes": { "summary": "增强钩子吸引力 | 优化CTTA | 增加数字元素" }
}
```

---

## 7. 组 3: 标题生成

### 7.1 POST /api/v1/titles/generate — 生成标题

为指定主题生成多个爆款标题，附带评分和钩子类型说明。

**请求体:**
```json
{
  "topic": "AI 绘画入门教程",
  "platform": "小红书",
  "count": 5
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| topic | string | 是 | - | 内容主题 |
| platform | string | 否 | "抖音" | 目标平台 |
| count | int | 否 | 5 | 标题数量(1-20) |

**响应:**
```json
[
  {
    "title": "零基础学 AI 绘画，3 天从小白到大神",
    "score": 95,
    "reason": "数字+利益，降低了用户心理门槛",
    "hook_type": "数字型"
  },
  {
    "title": "我花 100 块买的 AI 绘画课，还不如看这篇",
    "score": 92,
    "reason": "对比手法制造反差，激发好奇",
    "hook_type": "反常识型"
  }
]
```

**curl 示例:**
```bash
curl -s -X POST http://localhost:8000/api/v1/titles/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"AI绘画入门","platform":"小红书","count":5}' \
  | python -m json.tool
```

---

## 8. 组 4: 内容评分

### 8.1 POST /api/v1/content/score — Fire Score 五维评分

从钩子力、信任度、完播力、转化力、情绪值五个维度对内容进行评分。

**请求体:**
```json
{
  "title": "零基础学 AI 绘画，3 天从小白到大神",
  "body": "大家好，今天给大家分享 AI 绘画的入门方法...",
  "platform": "小红书"
}
```

**响应:**
```json
{
  "hook": 85,
  "trust": 78,
  "retention": 82,
  "conversion": 76,
  "emotion": 80,
  "total": 80,
  "level": "Lv2 稳爆",
  "suggestions": [
    "增强开头钩子，加入反常识数据",
    "增加具体案例增加可信度",
    "优化结尾CTA让转化更自然"
  ],
  "analysis": "内容整体质量较高，钩子和情绪维度表现优秀，建议在信任度和转化力上做进一步优化。"
}
```

**评分等级说明:**

| 等级 | 分数范围 | 说明 |
|------|----------|------|
| Lv1 必爆 | 90-100 | 内容质量极佳，大概率成为爆款 |
| Lv2 稳爆 | 80-89 | 内容质量优秀，爆款潜力大 |
| Lv3 高爆 | 70-79 | 内容质量良好，有爆款可能 |
| Lv4 普爆 | 60-69 | 内容质量一般，需要优化 |
| Lv5 基础 | <60 | 内容质量偏低，建议大幅改写 |

**curl 示例:**
```bash
curl -s -X POST http://localhost:8000/api/v1/content/score \
  -H "Content-Type: application/json" \
  -d '{"title":"零基础学AI绘画","body":"大家好...","platform":"小红书"}' \
  | python -m json.tool
```

---

## 9. 组 5: Fire Score 校准

### 9.1 POST /api/v1/fire-score/report — 上报发布数据

用户上报发布后的实际表现数据，触发 Fire Score 权重校准。

**请求体:**
```json
{
  "content_id": "content_abc123",
  "user_id": "user_xyz",
  "platform": "抖音",
  "fire_score": 82.5,
  "dimension_scores": {"hook": 85, "trust": 78, "retention": 82, "conversion": 76, "emotion": 80},
  "views": 15000,
  "likes": 1234,
  "comments": 567,
  "shares": 89,
  "favorites": 234
}
```

**响应:**
```json
{
  "engagement_rate": 0.126,
  "calibration": {
    "status": "calibrated",
    "weights": {"hook": 28.5, "trust": 18.2, "retention": 26.1, "conversion": 14.3, "emotion": 12.9},
    "correlations": {"hook": 0.42, "trust": 0.31, "retention": 0.38, "conversion": 0.22, "emotion": 0.19},
    "sample_count": 15,
    "calibrated_at": "2026-06-26T10:00:00"
  }
}
```

### 9.2 GET /api/v1/fire-score/weights/{platform} — 获取权重

获取指定平台当前的 Fire Score 校准权重。

**查询参数:** `user_id` (string, 默认 "default")

**请求示例:**
```bash
curl -s "http://localhost:8000/api/v1/fire-score/weights/%E6%8A%96%E9%9F%B3?user_id=user_xyz" | python -m json.tool
```

**响应:**
```json
{
  "user_id": "user_xyz",
  "platform": "抖音",
  "weights": {"hook": 28.5, "trust": 18.2, "retention": 26.1, "conversion": 14.3, "emotion": 12.9},
  "recent_content_count": 5
}
```

### 9.3 POST /api/v1/fire-score/calibrate — 手动触发校准

手动触发权重校准计算。

**请求体:**
```json
{
  "user_id": "user_xyz",
  "platform": "抖音"
}
```

**响应:**
```json
{
  "calibration": {
    "status": "calibrated",
    "weights": {"hook": 28.5, "trust": 18.2, "retention": 26.1, "conversion": 14.3, "emotion": 12.9},
    "correlations": {"hook": 0.42, "trust": 0.31, "retention": 0.38, "conversion": 0.22, "emotion": 0.19},
    "sample_count": 15,
    "calibrated_at": "2026-06-26T10:00:00"
  },
  "accuracy": {
    "avg_fire_score": 78.5,
    "avg_engagement_rate": 0.12,
    "prediction_accuracy": 0.85
  }
}
```

---

## 10. 组 6: 爆款监控/规则

### 10.1 GET /api/v1/monitor/rules — 获取所有平台规则

**响应:**
```json
{
  "updated_at": "2026-06-26T10:00:00",
  "platforms": ["抖音", "小红书", "B站"],
  "rules": {
    "抖音": { "platform": "抖音", "title_rules": [...], "hook_patterns": [...], "best_practices": [...] },
    "小红书": { ... }
  }
}
```

### 10.2 GET /api/v1/monitor/rules/{platform} — 获取单平台规则

**请求示例:**
```bash
curl -s http://localhost:8000/api/v1/monitor/rules/%E6%8A%96%E9%9F%B3 | python -m json.tool
```

### 10.3 POST /api/v1/monitor/rules/refresh — 手动刷新规则

触发所有平台规则的重新采集和更新。

**响应:**
```json
{
  "status": "ok",
  "platforms": ["抖音", "小红书", "B站", "微博", "知乎", "头条", "快手", "YouTube", "TikTok", "公众号", "视频号", "百度热搜", "Instagram"]
}
```

### 10.4 GET /api/v1/monitor/rules/status — 规则状态检查

返回每条规则的时效性状态。

**响应:**
```json
{
  "抖音": {"exists": true, "age_hours": 2.5, "status": "fresh"},
  "小红书": {"exists": true, "age_hours": 24.3, "status": "stale"}
}
```

---

## 11. 组 7: 视频生成

### 11.1 POST /api/v1/video/generate — 生成视频包

生成包含音频、字幕、封面的完整视频包。

**请求体:**
```json
{
  "script": "大家好，今天给大家分享 AI 绘画的入门方法...",
  "title": "AI 绘画入门教程",
  "platform": "抖音",
  "duration": 60
}
```

### 11.2 POST /api/v1/video/audio — 生成 TTS 音频

仅生成语音音频。

**响应:** `{"audio": "/data/videos/audio_xxx.mp3"}`

### 11.3 POST /api/v1/video/cover — 生成封面

**响应:** `{"cover": "/data/videos/cover_xxx.png"}`

### 11.4 POST /api/v1/video/digital-human — 生成数字人视频

使用 SiliconFlow 集成生成数字人播报视频。

**请求体:**
```json
{
  "script": "大家好，欢迎收看本期视频...",
  "title": "数字人播报测试",
  "platform": "抖音",
  "persona": "学长型",
  "duration": 60
}
```

**响应:**
```json
{
  "video_url": "https://...",
  "audio_url": "https://...",
  "duration": 60,
  "persona": "学长型"
}
```

---

## 12. 组 8: 数据闭环

### 12.1 POST /api/v1/analytics/publish — 记录发布事件

```json
{
  "project_id": "proj_xxx",
  "platform": "抖音",
  "title": "AI 工具推荐",
  "content_id": "content_abc",
  "fire_score": 85
}
```

### 12.2 POST /api/v1/analytics/{project_id}/{content_id}/metrics — 更新表现数据

```json
{
  "metrics": {"views": 15000, "likes": 1234, "comments": 567, "shares": 89, "saves": 234, "follows": 45, "watch_time": 3600}
}
```

### 12.3 GET /api/v1/analytics/{project_id} — 获取项目分析

**响应:**
```json
{
  "total_content": 10,
  "total_views": 150000,
  "total_likes": 12340,
  "total_comments": 5670,
  "total_shares": 890,
  "avg_engagement": 12.6,
  "content_list": [...]
}
```

### 12.4 GET /api/v1/analytics/platforms/summary — 平台汇总

**响应:**
```json
{
  "抖音": {"count": 5, "views": 100000, "likes": 8000},
  "小红书": {"count": 3, "views": 50000, "likes": 4340}
}
```

### 12.5 GET /api/v1/analytics/fire-score/{project_id} — 获取平均 Fire Score

```json
{"project_id": "proj_xxx", "avg_fire_score": 82.5}
```

---

## 13. 组 9: A/B 测试

### 13.1 GET /api/v1/ab-test/list — 列出所有测试

**响应:**
```json
{
  "tests": [{"test_id": "test_xxx", "project_id": "proj_xxx", "variants": [...], "status": "running", "created_at": "...", "winner": null}],
  "total": 1
}
```

### 13.2 POST /api/v1/ab-test/create — 创建测试

**请求体:**
```json
{
  "test_id": "test_001",
  "project_id": "proj_001",
  "variants": [
    {"title": "标题方案 A", "content": "内容版本 A..."},
    {"title": "标题方案 B", "content": "内容版本 B..."}
  ]
}
```

### 13.3 POST /api/v1/ab-test/{test_id}/update — 更新变体数据

```json
{"variant_id": "variant_0", "metrics": {"views": 1000, "likes": 100, "comments": 50, "shares": 20}}
```

### 13.4 GET /api/v1/ab-test/{test_id}/result — 获取测试结果

**响应:** 返回胜出变体和所有变体数据。

---

## 14. 组 10: 内容调度

### 14.1 POST /api/v1/calendar/schedule — 调度一次性发布

```json
{
  "project_id": "proj_001",
  "content_id": "content_abc",
  "platform": "抖音",
  "title": "AI 工具推荐",
  "content": "正文内容...",
  "scheduled_at": "2026-07-01T10:00:00"
}
```

### 14.2 POST /api/v1/calendar/recurring — 调度周期性发布

```json
{
  "project_id": "proj_001",
  "platform": "抖音",
  "title_template": "每日AI资讯 - {date}",
  "cron": "0 9 * * *"
}
```

**cron 格式:** `分 时 日 月 周`

| 示例 | 说明 |
|------|------|
| `0 9 * * *` | 每天 9:00 |
| `30 8 * * 1-5` | 工作日 8:30 |
| `0 10 * * 1` | 每周一 10:00 |
| `0 0 1 * *` | 每月 1 日 0:00 |

### 14.3 GET /api/v1/calendar/{year}/{month} — 获取日历视图

```bash
curl -s http://localhost:8000/api/v1/calendar/2026/7 | python -m json.tool
```

```json
{"year": 2026, "month": 7, "count": 5}
```

### 14.4 GET /api/v1/calendar/queue — 获取调度队列

返回所有已调度但未发布的任务列表。

### 14.5 DELETE /api/v1/calendar/{job_id} — 取消调度任务

```json
{"cancelled": true, "job_id": "proj_001_content_abc_1719360000"}
```

---

## 15. 组 11: 图像生成

### 15.1 POST /api/v1/image/generate — 生成图像

```json
{
  "prompt": "一只可爱的橘猫在阳光下打盹",
  "provider": "dalle",
  "size": "1024x1024",
  "n": 1
}
```

| 字段 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| prompt | 是 | - | 图像描述提示词 |
| provider | 否 | "dalle" | 生成服务: `dalle` / `stability` / `siliconflow` |
| size | 否 | "1024x1024" | 图像尺寸 |
| n | 否 | 1 | 生成数量 (1-4) |

**响应:** `{"images": ["https://..."], "provider": "dalle"}`

### 15.2 POST /api/v1/image/cover — 生成封面图

```json
{
  "title": "零基础学AI绘画",
  "platform": "小红书",
  "style": "现代简约"
}
```

**响应:** `{"cover": "/data/images/cover_xxx.png"}`

---

## 16. 组 12: 模板系统

### 16.1 GET /api/v1/templates/list — 列出模板

**查询参数:** `category` (可选), `platform` (可选)

**curl 示例:**
```bash
curl -s "http://localhost:8000/api/v1/templates/list?category=%E6%95%99%E7%A8%8B&platform=%E6%8A%96%E9%9F%B3" | python -m json.tool
```

### 16.2 GET /api/v1/templates/{template_id} — 获取模板详情

```bash
curl -s http://localhost:8000/api/v1/templates/tutorial_basic | python -m json.tool
```

### 16.3 POST /api/v1/templates/ — 保存模板

```json
{
  "id": "my_template_001",
  "name": "我的自定义模板",
  "category": "教程",
  "platform": "抖音",
  "structure": [{"section": "hook", "duration": 3, "template": "你知道{topic}吗？"}]
}
```

### 16.4 POST /api/v1/templates/apply — 应用模板

```json
{
  "template_id": "tutorial_basic",
  "variables": {
    "topic": "AI 绘画",
    "problem_point": "不知道从哪里开始",
    "step1": "选择合适的工具",
    "step2": "学习基础提示词",
    "step3": "多练习多尝试"
  }
}
```

---

## 17. 组 13: 自主 Agent

### 17.1 POST /api/v1/agent/create — 创建自动发布任务

```json
{
  "project_id": "proj_001",
  "platform": "抖音",
  "topic": "每日 AI 资讯",
  "frequency": "daily",
  "time_of_day": "10:00"
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| frequency | 否 | `daily` (每天) / `weekly` (每周一) |
| time_of_day | 否 | 发布时间 (HH:MM 格式) |

**响应:** 返回创建的任务对象，包含 `task_id` 和 cron 表达式。

### 17.2 GET /api/v1/agent/tasks — 获取所有任务

**响应:** 返回所有自动发布任务的数组。

### 17.3 GET /api/v1/agent/activity — 获取活动日志

**查询参数:** `limit` (int, 默认 100)

**响应:**
```json
{
  "log": [
    "2026-06-26T10:00:00 - 创建自动任务: 每日 AI 资讯 (抖音, daily 10:00)",
    "2026-06-25T10:00:00 - 矩阵优化完成: proj_001, 2 条建议"
  ]
}
```

---

## 18. 组 14: 团队协作

### 18.1 POST /api/v1/team/create — 创建团队

```json
{
  "name": "内容创作组",
  "owner_id": "user_xyz"
}
```

**响应:** 返回完整团队对象，包含 `team_id`、`members` 列表和创建时间。

### 18.2 POST /api/v1/team/invite — 邀请成员

```json
{
  "team_id": "team_abc",
  "email": "colleague@example.com",
  "role": "member"
}
```

| 字段 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| team_id | 是 | - | 团队 ID |
| email | 是 | - | 被邀请人邮箱 |
| role | 否 | "member" | `owner` / `admin` / `member` |

**响应:** 返回邀请对象，包含有效期 7 天的 `token`。

### 18.3 POST /api/v1/team/accept — 接受邀请

```json
{
  "token": "邀请令牌",
  "user_id": "user_abc"
}
```

### 18.4 GET /api/v1/team/user/{user_id} — 列出用户团队

```bash
curl -s http://localhost:8000/api/v1/team/user/user_xyz | python -m json.tool
```

### 18.5 GET /api/v1/team/{team_id} — 获取团队详情

```bash
curl -s http://localhost:8000/api/v1/team/team_abc | python -m json.tool
```

---

## 19. 组 15: 模型路由

### 19.1 POST /api/v1/router/chat — 路由聊天

将请求路由到最优模型（基于成本/质量/速度综合决策）。

```json
{
  "prompt": "介绍一下人工智能的发展历史",
  "system": "你是专业的 AI 科普专家",
  "task_type": "content_generation",
  "priority": "balanced"
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| prompt | string | 是 | - | 用户提示词 |
| system | string | 否 | "" | 系统提示词 |
| task_type | string | 否 | "content_generation" | 任务类型 |
| priority | string | 否 | "balanced" | `cost` / `quality` / `speed` / `balanced` |

**支持的任务类型:**

| 枚举值 | 说明 |
|--------|------|
| `content_generation` | 内容生成（长文） |
| `title_generation` | 标题生成（短文） |
| `scoring` | 评分（结构化输出） |
| `analysis` | 分析（深度推理） |
| `creative` | 创意（高创造性） |
| `translation` | 翻译 |
| `chat` | 聊天 |

**响应:**
```json
{
  "result": "...AI 生成的回答内容...",
  "model": "deepseek",
  "model_name": "DeepSeek Chat",
  "task_type": "content_generation",
  "usage": {"prompt_tokens": 150, "completion_tokens": 500}
}
```

### 19.2 GET /api/v1/router/profiles — 列出模型档案

```bash
curl -s http://localhost:8000/api/v1/router/profiles | python -m json.tool
```

**响应 (节选):**
```json
{
  "deepseek": {
    "name": "DeepSeek Chat",
    "cost_per_1k": 0.001,
    "avg_latency_ms": 2500,
    "quality": 0.9,
    "max_tokens": 4096,
    "best_for": ["content_generation", "analysis", "chat"]
  }
}
```

### 19.3 GET /api/v1/router/recommend — 推荐模型

**查询参数:** `task_type` (默认 "content_generation"), `priority` (默认 "balanced")

```bash
curl -s "http://localhost:8000/api/v1/router/recommend?task_type=scoring&priority=cost" | python -m json.tool
```

```json
{"recommended": "ernie", "source": "static"}
```

### 19.4 GET /api/v1/router/stats — 路由统计

返回所有模型的历史调用统计。

### 19.5 GET /api/v1/router/performance — 模型性能

**查询参数:** `model_name` (可选，不传则返回所有)

### 19.6 POST /api/v1/router/cost-estimate — 成本估算

```bash
curl -s -X POST "http://localhost:8000/api/v1/router/cost-estimate?prompt=%E4%BB%8B%E7%BB%8DAI&model_name=deepseek&output_tokens=500" | python -m json.tool
```

```json
{"estimated_cost": 0.0023, "model_name": "deepseek", "model_display": "DeepSeek Chat", "output_tokens": 500}
```

---

## 20. 组 16: 内容洞察

### 20.1 GET /api/v1/insights/trends/{platform} — 平台趋势分析

```bash
curl -s "http://localhost:8000/api/v1/insights/trends/%E6%8A%96%E9%9F%B3?days=7" | python -m json.tool
```

**响应:**
```json
{
  "platform": "抖音",
  "trends": [
    {"type": "hook_pattern", "name": "数字型", "count": 15, "direction": "rising"},
    {"type": "hook_pattern", "name": "悬念型", "count": 12, "direction": "stable"}
  ],
  "hot_topics": ["AI工具", "副业赚钱", "减肥方法"],
  "title_patterns": [...],
  "summary": "过去7天共分析10种钩子模式"
}
```

### 20.2 GET /api/v1/insights/predict/{platform} — 预测爆款话题

```bash
curl -s http://localhost:8000/api/v1/insights/predict/%E5%B0%8F%E7%BA%A2%E4%B9%A6 | python -m json.tool
```

**响应:**
```json
{
  "platform": "小红书",
  "predictions": [
    {"topic": "AI绘画教程", "viral_score": 92, "reason": "匹配8种爆款钩子模式", "suggested_hook": "数字型"},
    {"topic": "副业月入过万", "viral_score": 88, "reason": "搜索量持续上升", "suggested_hook": "痛点型"}
  ]
}
```

### 20.3 POST /api/v1/insights/recommendations — 获取内容建议

```json
{
  "topic": "AI 工具推荐",
  "platform": "抖音"
}
```

**响应:**
```json
{
  "topic": "AI 工具推荐",
  "platform": "抖音",
  "hook_type": "数字型",
  "best_duration": 60,
  "title_templates": [...],
  "best_practices": ["前3秒用数字钩子", "加入对比效果展示"]
}
```

### 20.4 GET /api/v1/insights/posting-time/{platform} — 最佳发布时间

```bash
curl -s http://localhost:8000/api/v1/insights/posting-time/%E6%8A%96%E9%9F%B3 | python -m json.tool
```

**响应:**
```json
{
  "platform": "抖音",
  "time_slots": [],
  "recommendation": "暂无抖音的最佳发布时机数据"
}
```

---

## 21. 组 17: 竞品监控

### 21.1 POST /api/v1/competitors/add — 添加竞品账号

```json
{
  "user_id": "user_xyz",
  "platform": "抖音",
  "account_id": "douyin_123456",
  "account_name": "竞品账号名称"
}
```

### 21.2 DELETE /api/v1/competitors/{competitor_id} — 移除竞品

```bash
curl -s -X DELETE http://localhost:8000/api/v1/competitors/abc123def456 | python -m json.tool
```

### 21.3 GET /api/v1/competitors/list — 列出竞品

**查询参数:** `user_id` (必填)

```bash
curl -s "http://localhost:8000/api/v1/competitors/list?user_id=user_xyz" | python -m json.tool
```

```json
{
  "competitors": [
    {"id": "abc123", "platform": "抖音", "account_name": "竞品A", "total_content": 50, "total_views": 500000}
  ]
}
```

### 21.4 GET /api/v1/competitors/analyze/{competitor_id} — 分析竞品

返回竞品的内容策略分析，包括主题分布、发布频率、风格分析等。

### 21.5 GET /api/v1/competitors/compare/{competitor_id} — 对比分析

**查询参数:** `user_id` (必填)

返回用户与竞品的表现差异对比。

### 21.6 POST /api/v1/competitors/record — 记录竞品内容

```json
{
  "competitor_id": "abc123",
  "content_data": {
    "content_id": "platform_001",
    "title": "竞品的爆款标题",
    "content_type": "视频",
    "published_at": "2026-06-25T10:00:00",
    "metrics": {"views": 100000, "likes": 5000, "comments": 2000, "shares": 1000, "saves": 3000},
    "topics": ["AI工具", "效率提升"],
    "style_tags": ["教程", "测评"],
    "summary": "视频内容摘要"
  }
}
```

---

## 22. 组 18: SSE 流式生成

### 22.1 POST /api/v1/stream/generate — 流式生成内容 (SSE)

以 Server-Sent Events 方式实时推送内容生成进度，无需等待完整响应。

**请求体:**
```json
{
  "topic": "AI 工具提升工作效率",
  "platform": "抖音",
  "persona": "学长型",
  "duration": 60,
  "priority": "balanced"
}
```

**SSE 事件流 (text/event-stream):**

```
data: {"event": "status", "data": {"message": "正在分析主题...", "progress": 10}}

data: {"event": "model", "data": {"model": "deepseek", "model_name": "DeepSeek Chat", "priority": "balanced"}}

data: {"event": "status", "data": {"message": "已选择模型: DeepSeek Chat", "progress": 20}}

data: {"event": "status", "data": {"message": "正在加载平台规则...", "progress": 30}}

data: {"event": "status", "data": {"message": "正在生成爆款标题...", "progress": 40}}

data: {"event": "title", "data": {"title": "打工人必看！3个AI工具让我效率翻倍"}}

data: {"event": "title", "data": {"title": "别再加班了，试试这些AI神器"}}

data: {"event": "status", "data": {"message": "标题生成完成，正在创作脚本...", "progress": 60}}

data: {"event": "status", "data": {"message": "正在逐段生成脚本...", "progress": 70}}

data: {"event": "chunk", "data": {"text": "你是不是也经常加班到深夜？", "accumulated": "你是不是也经常加班到深夜？"}}

data: {"event": "chunk", "data": {"text": "今天给大家推荐3个超实用的AI工具。", "accumulated": "你是不是也经常加班到深夜？今天给大家推荐3个超实用的AI工具。"}}

data: {"event": "complete", "data": {"titles": [...], "script": "...", "subtitles": [...], "tags": [...], "hook": "...", "call_to_action": "..."}}

data: {"event": "status", "data": {"message": "生成完成", "progress": 100, "duration_ms": 15234}}
```

**事件类型说明:**

| 事件类型 | 说明 |
|----------|------|
| `status` | 状态更新，包含进度百分比 |
| `model` | 选中的模型信息 |
| `title` | 生成的单个标题 |
| `chunk` | 脚本段落片段 |
| `complete` | 完整的最终结果 |
| `error` | 生成出错 |

**curl 示例 (流式监听):**
```bash
curl -N -X POST http://localhost:8000/api/v1/stream/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"AI工具","platform":"抖音","persona":"学长型","duration":60}' \
  --no-buffer
```

**前端 JavaScript 示例:**
```javascript
const eventSource = new EventSource('/api/v1/stream/generate', {
  method: 'POST',
  body: JSON.stringify({ topic: "AI工具", platform: "抖音" }),
  headers: { 'Content-Type': 'application/json' }
});

// 实际使用 fetch + ReadableStream 读取 SSE
const response = await fetch('/api/v1/stream/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ topic: "AI工具" })
});
const reader = response.body.getReader();
// ...
```

**Nginx 注意:** SSE 端点需要禁用缓冲，已在 Nginx 配置中处理 (`proxy_buffering off;`)。

---

## 附录 A: 平台列表

支持的平台列表，共 16 个:

| 平台名称 | API 编码 |
|----------|----------|
| 抖音 | `抖音` |
| 小红书 | `小红书` |
| B站 | `B站` |
| 公众号 | `公众号` |
| YouTube | `YouTube` |
| TikTok | `TikTok` |
| 快手 | `快手` |
| 微博 | `微博` |
| 知乎 | `知乎` |
| 头条 | `头条` |
| 视频号 | `视频号` |
| Instagram | `Instagram` |
| Twitter | `Twitter` |
| 企鹅号 | `企鹅号` |
| 大鱼号 | `大鱼号` |
| 百家号 | `百家号` |

---

## 附录 B: 限流策略

| 端点 | 限制 | 窗口 |
|------|------|------|
| `/api/v1/content/generate` | 30 次/平台 | 60 秒 |
| 所有其他端点 | 60 次 | 60 秒 |
| 未认证请求 | 10 次 | 60 秒 |

限流响应: HTTP 429 + `{"detail": "请求过于频繁"}`

---

## 附录 C: 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.7.0 | 2026-06-26 | 完整 18 组 API，SSE 流式输出，Fire Score 校准引擎 |
| 0.5.0 | 2026-05 | 初始 API 版本，12 组路由 |
