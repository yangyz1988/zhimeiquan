import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.deepseek import DeepSeekClient
from services.prompts import Prompts
from monitors.scheduler import RuleScheduler

router = APIRouter()
client = DeepSeekClient()
scheduler = RuleScheduler(data_dir="../data/rules")


class ScoreRequest(BaseModel):
    title: str
    body: str
    platform: str = "抖音"


class ScoreResponse(BaseModel):
    hook: int
    trust: int
    retention: int
    conversion: int
    emotion: int
    total: int
    level: str
    suggestions: list[str]
    analysis: str


@router.post("/score", response_model=ScoreResponse)
async def score_content(req: ScoreRequest):
    """Fire Score 五维评分（结合实时爆款规则）"""
    if not client.api_key:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY 未配置")

    try:
        # 加载该平台的爆款规则
        rules = scheduler.load_rules(req.platform)

        system, prompt = Prompts.score_content(
            title=req.title,
            body=req.body,
            platform=req.platform,
            rules=rules if rules else None,
        )
        result = await client.chat(prompt, system=system)
        data = json.loads(result)
        return ScoreResponse(**data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI 返回格式错误")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
