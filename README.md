# 智媒圈 - AI自媒体内容工厂

> 输入主题，30秒拿走成品 | 13平台覆盖 | 数据驱动

---

## 核心特性

- **30秒生成爆款内容** - 口播稿+字幕+标题+封面，一键搞定
- **Fire Score 五维评分** - 钩子力/信任度/完播力/转化力/情绪值
- **13平台算法适配** - 抖音/小红书/B站/公众号/YouTube/TikTok...
- **6大AI引擎驱动** - 文案/配图/脚本/拆解/数据/优化
- **数据回流自动优化** - 发布→数据→校准→更准的预测

---

## 项目结构

```
zhimeiquan/
├── saas/                  # Next.js SaaS 平台
│   ├── src/               # 源代码
│   ├── prisma/            # 数据库
│   └── public/            # 静态资源
│
├── content/               # 内容知识库
│   ├── methodology/       # 方法论体系
│   ├── templates/         # 模板库
│   └── experts/           # 专家资源库
│
├── scripts/               # Python 生成服务
│   ├── generators/        # 内容生成器
│   ├── analyzers/         # 数据分析
│   └── automation/        # 自动化工具
│
├── deploy/                # 部署配置
│   └── nginx/             # Nginx 配置
│
└── docs/                  # 项目文档
```

---

## 快速开始

### Docker Compose（推荐）

```bash
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY
docker compose up -d
# Next.js: http://localhost:3000
# API: http://localhost:8000/docs
```

### 本地开发

```bash
# Next.js
cd saas && pnpm install && pnpm dev

# Python 服务
cd scripts && pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### PowerShell 快速启动

```powershell
.\start.ps1
```

---

## 技术栈

| 层级 | 技术 |
|:-----|:-----|
| 前端 | Next.js 16 + React 19 + Tailwind CSS 4 + shadcn/ui |
| 后端 | Prisma 6 + PostgreSQL |
| AI | DeepSeek API |
| TTS | Edge TTS |
| 视频 | FFmpeg + Pillow |
| 缓存 | Redis |
| 部署 | Docker + Nginx |

---

## API 接口

```bash
# 内容生成
curl -X POST http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI时代普通人如何做自媒体", "platform": "抖音", "persona": "学长型", "duration": 60}'

# 标题生成
curl -X POST http://localhost:8000/api/v1/titles/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "自媒体赚钱", "platform": "抖音", "count": 5}'

# 内容评分
curl -X POST http://localhost:8000/api/v1/content/score \
  -H "Content-Type: application/json" \
  -d '{"title": "3个底层逻辑", "body": "你以为做自媒体就是...", "platform": "抖音"}'
```

完整 API 文档：http://localhost:8000/docs

---

## Fire Score 评分系统

| 维度 | 权重 | 说明 |
|:-----|:----:|:-----|
| 钩子力 | 25% | 前3秒能否让人停住 |
| 信任度 | 20% | 内容是否可信、有依据 |
| 完播力 | 20% | 节奏是否紧凑、不无聊 |
| 转化力 | 20% | 用户看完会不会关注/收藏 |
| 情绪值 | 15% | 有没有情绪共鸣 |

## 爆款等级体系

| 等级 | 概率 | 资源投入 |
|:-----|:----:|:---------|
| Lv1 必爆 | 100% | 投流+矩阵+私域全开 |
| Lv2 稳爆 | 90% | A/B测试+矩阵分发 |
| Lv3 高爆 | 80% | 全量分发+私域启动 |
| Lv4 普爆 | 70% | 单号深耕+卡点发布 |
| Lv5 基础 | 60% | 快速生成+自然发布 |

---

## License

MIT
