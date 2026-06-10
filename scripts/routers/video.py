"""视频生成 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.video import VideoGenerator

router = APIRouter()
generator = VideoGenerator(output_dir="../data/videos")


class VideoRequest(BaseModel):
    script: str
    title: str
    platform: str = "抖音"
    duration: int = 60


@router.post("/generate")
async def generate_video(req: VideoRequest):
    """生成视频包（音频+字幕+封面）"""
    try:
        result = await generator.generate_video_package(
            script=req.script,
            title=req.title,
            platform=req.platform,
            duration=req.duration,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="视频生成失败，请稍后重试")


@router.post("/audio")
async def generate_audio(req: VideoRequest):
    """仅生成 TTS 音频"""
    try:
        audio_path = await generator.generate_audio(req.script, req.platform)
        return {"audio": audio_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail="音频生成失败，请稍后重试")


@router.post("/cover")
async def generate_cover(req: VideoRequest):
    """仅生成封面"""
    try:
        cover_path = generator.generate_cover(req.title, req.platform)
        return {"cover": cover_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail="封面生成失败，请稍后重试")


class DigitalHumanRequest(BaseModel):
    script: str
    title: str
    platform: str = "抖音"
    persona: str = "学长型"
    duration: int = 60


@router.post("/digital-human")
async def generate_digital_human_video(req: DigitalHumanRequest):
    """生成数字人视频"""
    from services.digital_human import DigitalHumanGenerator

    dh_generator = DigitalHumanGenerator()
    try:
        result = await dh_generator.generate_from_persona(
            text=req.script,
            persona=req.persona,
            platform=req.platform,
        )
        return {**result, "persona": req.persona}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="数字人视频生成失败，请稍后重试")
