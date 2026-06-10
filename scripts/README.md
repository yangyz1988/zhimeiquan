# Python 脚本服务

FastAPI v0.5.0 后端，AI 内容策略引擎。

## 目录结构

- `services/` — 核心业务逻辑（DeepSeek 对接、Fire Score 评分、内容生成、视频/图像生成、数据回流等）
- `routers/` — FastAPI 路由（content / titles / score / video / image / analytics / ab_test / calendar / agent / team / templates / insights / health）
- `monitors/` — 热榜爬取 + 数据分析 + 定时调度（scraper / analyzer / scheduler）
- `tests/` — pytest 测试套件（44 用例）

## 启动

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## 测试

```bash
python -m pytest tests/ -v
```

## API 文档

启动后访问 http://localhost:8000/docs
