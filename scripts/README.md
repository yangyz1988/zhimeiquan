# Python 脚本服务

## 目录说明

- `generators/` - 内容生成器，对接 DeepSeek API
- `analyzers/` - 数据分析，Fire Score 评分
- `automation/` - 自动化工具，定时任务
- `routers/` - FastAPI 路由

## 启动

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## API 文档

启动后访问 http://localhost:8000/docs
