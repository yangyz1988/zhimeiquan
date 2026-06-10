"""AI 数字人视频生成服务 - 基于 SiliconFlow"""

import os
from pathlib import Path

import httpx

from services.cache import CacheService
from services.error_handler import retry
from services.logging import logger


class DigitalHumanGenerator:
    """AI 数字人视频生成器"""

    API_URL = "https://api.siliconflow.cn/v1/video/generations"

    AVATAR_PRESETS: dict[str, dict] = {
        "学长型": {
            "avatar_id": "avatar_male_01",
            "voice_id": "zh-CN-YunxiNeural",
            "name": "阳光学长",
        },
        "学姐型": {
            "avatar_id": "avatar_female_01",
            "voice_id": "zh-CN-XiaoxiaoNeural",
            "name": "知性学姐",
        },
        "专家型": {
            "avatar_id": "avatar_male_02",
            "voice_id": "zh-CN-YunjianNeural",
            "name": "专业导师",
        },
        "闺蜜型": {
            "avatar_id": "avatar_female_02",
            "voice_id": "zh-CN-XiaoyiNeural",
            "name": "贴心闺蜜",
        },
        "老铁型": {
            "avatar_id": "avatar_male_03",
            "voice_id": "zh-CN-YunxiNeural",
            "name": "接地气老铁",
        },
        "导师型": {
            "avatar_id": "avatar_male_02",
            "voice_id": "zh-CN-YunjianNeural",
            "name": "资深导师",
        },
        "吐槽型": {
            "avatar_id": "avatar_male_01",
            "voice_id": "zh-CN-YunxiNeural",
            "name": "犀利吐槽",
        },
        "故事型": {
            "avatar_id": "avatar_female_01",
            "voice_id": "zh-CN-XiaoxiaoNeural",
            "name": "故事讲述",
        },
        "干货型": {
            "avatar_id": "avatar_male_02",
            "voice_id": "zh-CN-YunjianNeural",
            "name": "干货达人",
        },
    }

    def __init__(self, output_dir: str = "../data/videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache = CacheService()

    @retry(max_attempts=3, delay=3.0, backoff=2.0, exceptions=(httpx.HTTPError,))
    async def generate_video(
        self,
        text: str,
        avatar_id: str,
        voice_id: str,
    ) -> dict:
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise ValueError("SILICONFLOW_API_KEY 未配置")

        cache_key = self.cache._make_key(
            "digital_human",
            {"text": text[:200], "avatar": avatar_id, "voice": voice_id},
        )
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "silicon-music/SiliconVideo-240214",
                    "prompt": text,
                    "avatar_id": avatar_id,
                    "voice_id": voice_id,
                },
            )
            response.raise_for_status()
            result = response.json()

        video_url = result.get("video_url") or result.get("data", [{}])[0].get(
            "url"
        )
        if not video_url:
            raise ValueError("视频生成失败：未返回视频 URL")

        output = {"video_url": video_url, "status": "completed"}
        await self.cache.set(cache_key, output, ttl=3600)
        return output

    async def generate_from_persona(
        self,
        text: str,
        persona: str,
        platform: str = "抖音",
    ) -> dict:
        preset = self.AVATAR_PRESETS.get(persona, self.AVATAR_PRESETS["学长型"])
        logger.info(
            "数字人视频生成",
            persona=persona,
            avatar=preset["avatar_id"],
            platform=platform,
        )
        return await self.generate_video(
            text=text,
            avatar_id=preset["avatar_id"],
            voice_id=preset["voice_id"],
        )
