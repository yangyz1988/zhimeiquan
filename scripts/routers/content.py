import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.deepseek import DeepSeekClient
from services.prompts import Prompts
from monitors.scheduler import RuleScheduler

router = APIRouter()
client = DeepSeekClient()
scheduler = RuleScheduler(data_dir="../data/rules")


class GenerateRequest(BaseModel):
    topic: str
    platform: str = "抖音"
    persona: str = "学长型"
    duration: int = 60


class GenerateResponse(BaseModel):
    titles: list[str]
    script: str
    subtitles: list[dict]
    tags: list[str]
    hook: str
    call_to_action: str


@router.post("/generate", response_model=GenerateResponse)
async def generate_content(req: GenerateRequest):
    """根据主题生成口播内容（结合实时爆款规则）"""
    if not client.api_key:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY 未配置")

    try:
        # 加载该平台的爆款规则
        rules = scheduler.load_rules(req.platform)

        system, prompt = Prompts.generate_content(
            topic=req.topic,
            platform=req.platform,
            persona=req.persona,
            duration=req.duration,
            rules=rules if rules else None,
        )
        result = await client.chat(prompt, system=system)
        data = json.loads(result)
        return GenerateResponse(**data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI 返回格式错误")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
