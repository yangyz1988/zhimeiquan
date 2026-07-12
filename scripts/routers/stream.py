"""SSE 流式内容生成 - 实时输出生成进度"""

import json
import time
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.router import default_router, TaskType, MODEL_PROFILES
from services.prompts import Prompts
from monitors.scheduler import RuleScheduler
from services.cache import CacheService, rate_limit
from services.logging import logger, track_time
from services.validators import validate_topic, validate_platform, validate_duration

router = APIRouter()
scheduler = RuleScheduler(data_dir="../data/rules")
cache = CacheService()


class StreamGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    platform: str = "抖音"
    persona: str = "学长型"
    duration: int = Field(60, ge=5, le=3600)
    priority: str = "balanced"


def sse_json(event: str, data: object) -> str:
    """构造 SSE 消息"""
    return f"data: {json.dumps({'event': event, 'data': data}, ensure_ascii=False)}\n\n"


async def generate_titles_stream(
    topic: str,
    platform: str,
    rules: dict | None,
) -> AsyncGenerator[str, None]:
    """模拟逐步生成标题（后续可改为单独的 streaming API）"""
    from services.deepseek import DeepSeekClient

    client = DeepSeekClient()
    system, prompt = Prompts.generate_titles(
        topic=topic, platform=platform, count=5, rules=rules
    )
    result = await client.chat(prompt, system=system)

    try:
        data = json.loads(result)
        titles = [t["title"] for t in data.get("titles", [])]
    except (json.JSONDecodeError, KeyError):
        titles = []

    for title in titles:
        yield sse_json("title", {"title": title})
        await __import__("asyncio").sleep(0.3)  # 模拟间隔


async def stream_script_generation(
    prompt: str,
    system: str,
    task_type: TaskType,
) -> AsyncGenerator[str, None]:
    """模拟流式脚本生成（使用模型路由后逐步返回段落）"""
    from services.deepseek import DeepSeekClient

    client = DeepSeekClient()
    result = await client.chat(prompt, system=system)

    # 按段落切分，模拟流式输出
    paragraphs = result.split("\n\n")
    accumulated = ""
    for i, para in enumerate(paragraphs):
        if para.strip():
            # 按句子切分，模拟逐句输出
            sentences = para.replace("。", "。\n").replace("！", "！\n").replace("？", "？\n").split("\n")
            for sentence in sentences:
                if sentence.strip():
                    accumulated += sentence.strip()
                    yield sse_json("chunk", {
                        "text": sentence.strip(),
                        "accumulated": accumulated,
                    })
                    await __import__("asyncio").sleep(0.1)

    # 最后输出完整结果，用于构建结构化响应
    try:
        data = json.loads(result)
        yield sse_json("complete", {
            "titles": data.get("titles", []),
            "script": data.get("script", ""),
            "subtitles": data.get("subtitles", []),
            "tags": data.get("tags", []),
            "hook": data.get("hook", ""),
            "call_to_action": data.get("call_to_action", ""),
        })
    except json.JSONDecodeError:
        # 如果不是严格 JSON，返回全文
        yield sse_json("complete", {"script": result})


@router.post("/generate")
async def stream_generate(req: StreamGenerateRequest, request: Request):
    """SSE 流式生成内容

    实时推送生成进度，包括：
    - status: 状态更新
    - model: 选择的模型
    - title: 生成的标题
    - chunk: 脚本段落
    - complete: 完成结果
    """
    topic = validate_topic(req.topic)
    platform = validate_platform(req.platform)
    duration = validate_duration(req.duration)

    async def event_generator():
        try:
            # 1. 状态：开始
            yield sse_json("status", {"message": "正在分析主题...", "progress": 10})
            await __import__("asyncio").sleep(0.3)

            # 2. 选择模型
            task = TaskType.CONTENT_GENERATION
            model_name = default_router.select_model(task, req.priority)
            profile = MODEL_PROFILES.get(model_name)
            yield sse_json("model", {
                "model": model_name,
                "model_name": profile.name if profile else model_name,
                "priority": req.priority,
            })
            yield sse_json("status", {"message": f"已选择模型: {profile.name if profile else model_name}", "progress": 20})
            await __import__("asyncio").sleep(0.3)

            # 3. 加载爆款规则
            rules = scheduler.load_rules(platform)
            yield sse_json("status", {"message": "正在加载平台规则...", "progress": 30})
            await __import__("asyncio").sleep(0.2)

            # 4. 生成标题（流式输出）
            yield sse_json("status", {"message": "正在生成爆款标题...", "progress": 40})
            async for title_msg in generate_titles_stream(topic, platform, rules):
                yield title_msg

            yield sse_json("status", {"message": "标题生成完成，正在创作脚本...", "progress": 60})

            # 5. 生成脚本
            system, prompt = Prompts.generate_content(
                topic=topic,
                platform=platform,
                persona=req.persona,
                duration=duration,
                rules=rules if rules else None,
            )

            # 增强提示词
            enhanced_prompt = default_router.enhance_prompt(prompt, task, model_name)
            if enhanced_prompt != prompt:
                system += "\n\n" + enhanced_prompt

            yield sse_json("status", {"message": "正在逐段生成脚本...", "progress": 70})

            start = time.time()
            async for chunk_msg in stream_script_generation(enhanced_prompt, system, task):
                yield chunk_msg

            duration_ms = (time.time() - start) * 1000

            # 记录路由结果
            default_router.record_result({
                "model_name": model_name,
                "task_type": task.value,
                "duration_ms": duration_ms,
                "success": True,
                "cost": default_router.estimate_cost(enhanced_prompt, model_name),
                "prompt_length": len(enhanced_prompt),
            })

            # 最终状态
            yield sse_json("status", {
                "message": "生成完成",
                "progress": 100,
                "duration_ms": duration_ms,
            })

        except Exception as e:
            logger.error("SSE 流式生成失败", error=str(e))
            yield sse_json("error", {"message": f"生成失败: {str(e)}"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
