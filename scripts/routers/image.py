"""图像生成 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.image_gen import ImageGenerator

router = APIRouter()
generator = ImageGenerator()


class ImageRequest(BaseModel):
    prompt: str
    provider: str = "dalle"
    size: str = "1024x1024"
    n: int = 1


class CoverRequest(BaseModel):
    title: str
    platform: str = "抖音"
    style: str = "现代简约"


@router.post("/generate")
async def generate_image(req: ImageRequest):
    """生成图像"""
    try:
        result = await generator.generate(
            prompt=req.prompt,
            provider=req.provider,
            size=req.size,
            n=req.n,
        )
        return {"images": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail="图像生成失败，请稍后重试")


@router.post("/cover")
async def generate_cover(req: CoverRequest):
    """为内容生成封面图"""
    try:
        cover_path = await generator.generate_cover_for_content(
            title=req.title,
            platform=req.platform,
            style=req.style,
        )
        return {"cover": cover_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail="封面生成失败，请稍后重试")
