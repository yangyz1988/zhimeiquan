import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.router import default_router, TaskType
from services.prompts import Prompts
from monitors.scheduler import RuleScheduler
from services.cache import CacheService, rate_limit
from services.logging import logger, track_time
from services.validators import validate_topic, validate_platform, validate_duration

router = APIRouter()
scheduler = RuleScheduler(data_dir="../data/rules")
cache = CacheService()


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    platform: str = "抖音"
    persona: str = "学长型"
    duration: int = Field(60, ge=5, le=3600)


class GenerateResponse(BaseModel):
    titles: list[str]
    script: str
    subtitles: list[dict]
    tags: list[str]
    hook: str
    call_to_action: str


@router.post("/generate", response_model=GenerateResponse)
@rate_limit(limit=30, window=60, key_func=lambda req, *_: f"generate:{req.platform}")
async def generate_content(req: GenerateRequest):
    """根据主题生成口播内容（结合实时爆款规则）"""

    # 输入验证
    topic = validate_topic(req.topic)
    platform = validate_platform(req.platform)
    duration = validate_duration(req.duration)

    with track_time("generate_content", platform=platform):
        try:
            # 加载该平台的爆款规则
            rules = scheduler.load_rules(platform)

            system, prompt = Prompts.generate_content(
                topic=topic,
                platform=platform,
                persona=req.persona,
                duration=duration,
                rules=rules if rules else None,
            )
            route_result = await default_router.route(
                prompt=prompt,
                system=system,
                task_type=TaskType.CONTENT_GENERATION,
            )
            result = route_result["result"]
            data = json.loads(result)
            logger.info("内容生成成功", topic=topic[:30], platform=platform, model=route_result["model"])
            return GenerateResponse(**data)
        except json.JSONDecodeError:
            logger.error("AI 返回格式错误", topic=topic[:30])
            raise HTTPException(status_code=500, detail="AI 返回格式错误")
        except Exception as e:
            logger.error("内容生成失败", error=str(e))
            raise HTTPException(status_code=500, detail="内容生成失败，请稍后重试")
