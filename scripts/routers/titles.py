import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.deepseek import DeepSeekClient
from services.prompts import Prompts
from monitors.scheduler import RuleScheduler

router = APIRouter()
client = DeepSeekClient()
scheduler = RuleScheduler(data_dir="../data/rules")


class TitleRequest(BaseModel):
    topic: str
    platform: str = "抖音"
    count: int = 5


class TitleItem(BaseModel):
    title: str
    score: int
    reason: str
    hook_type: str


@router.post("/generate", response_model=list[TitleItem])
async def generate_titles(req: TitleRequest):
    """生成爆款标题（结合实时爆款规则）"""
    if not client.api_key:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY 未配置")

    try:
        # 加载该平台的爆款规则
        rules = scheduler.load_rules(req.platform)

        system, prompt = Prompts.generate_titles(
            topic=req.topic,
            platform=req.platform,
            count=req.count,
            rules=rules if rules else None,
        )
        result = await client.chat(prompt, system=system)
        data = json.loads(result)
        return [TitleItem(**t) for t in data["titles"]]
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI 返回格式错误")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
