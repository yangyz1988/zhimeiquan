from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import content, titles, score, rules

app = FastAPI(
    title="智媒圈 API",
    description="AI自媒体内容工厂 - 后端服务",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(content.router, prefix="/api/v1/content", tags=["内容生成"])
app.include_router(titles.router, prefix="/api/v1/titles", tags=["标题生成"])
app.include_router(score.router, prefix="/api/v1/content", tags=["内容评分"])
app.include_router(rules.router, prefix="/api/v1/monitor", tags=["爆款监控"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}
