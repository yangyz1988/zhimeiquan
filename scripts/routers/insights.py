"""内容洞察 API"""

from fastapi import APIRouter
from pydantic import BaseModel

from services.insights import ContentInsightsEngine

router = APIRouter()
engine = ContentInsightsEngine()


class RecommendationRequest(BaseModel):
    topic: str
    platform: str = "抖音"


@router.get("/trends/{platform}")
async def get_trends(platform: str, days: int = 7):
    """获取平台趋势分析"""
    return engine.analyze_trends(platform, days)


@router.get("/predict/{platform}")
async def predict_viral(platform: str):
    """预测爆款话题"""
    return engine.predict_viral_topic(platform)


@router.post("/recommendations")
async def get_recommendations(req: RecommendationRequest):
    """获取内容建议"""
    return engine.get_content_recommendations(req.topic, req.platform)


@router.get("/posting-time/{platform}")
async def get_posting_time(platform: str):
    """获取最佳发布时机"""
    return engine.get_optimal_posting_time(platform)
