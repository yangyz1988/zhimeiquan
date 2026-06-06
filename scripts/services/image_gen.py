"""AI 图像生成服务 - 封面图、配图"""

import base64
import os
from datetime import datetime
from pathlib import Path

import httpx

from services.cache import CacheService
from services.error_handler import retry
from services.logging import logger


class ImageGenerator:
    """AI 图像生成器"""

    PROVIDERS = {
        "dalle": {
            "url": "https://api.openai.com/v1/images/generations",
            "model": "dall-e-3",
        },
        "stability": {
            "url": "https://api.stability.ai/v2beta/stable-image/generate/sd3",
            "model": "sd3",
        },
        "siliconflow": {
            "url": "https://api.siliconflow.cn/v1/images/generations",
            "model": "Kwai-Kolors/Kolors",
        },
    }

    def __init__(self, output_dir: str = "../data/images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache = CacheService()

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(httpx.HTTPError,))
    async def generate(
        self,
        prompt: str,
        provider: str = "dalle",
        size: str = "1024x1024",
        n: int = 1,
    ) -> list[dict]:
        """生成图像"""
        cache_key = self.cache._make_key(
            f"image:{provider}",
            {
                "prompt": prompt[:300],
                "size": size,
                "n": n,
            },
        )

        cached = await self.cache.get(cache_key)
        if cached is not None:
            logger.info("图像缓存命中", provider=provider)
            return cached

        provider_config = self.PROVIDERS.get(provider)
        if not provider_config:
            raise ValueError(f"不支持的图像服务: {provider}")

        api_key_env = {
            "dalle": "OPENAI_API_KEY",
            "stability": "STABILITY_API_KEY",
            "siliconflow": "SILICONFLOW_API_KEY",
        }.get(provider)

        api_key = os.getenv(api_key_env, "")
        if not api_key:
            raise ValueError(f"{api_key_env} 未配置")

        if provider == "dalle":
            result = await self._generate_dalle(prompt, api_key, size, n)
        elif provider == "stability":
            result = await self._generate_stability(prompt, api_key, size)
        elif provider == "siliconflow":
            result = await self._generate_siliconflow(prompt, api_key, size, n)

        await self.cache.set(cache_key, result, ttl=86400)
        return result

    async def _generate_dalle(
        self, prompt: str, api_key: str, size: str, n: int
    ) -> list[dict]:
        """DALL-E 3"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                self.PROVIDERS["dalle"]["url"],
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": n,
                    "size": size,
                    "response_format": "b64_json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for i, item in enumerate(data["data"]):
                filepath = (
                    self.output_dir / f"dalle_{int(datetime.now().timestamp())}_{i}.png"
                )
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(item["b64_json"]))
                results.append(
                    {"url": str(filepath), "provider": "dalle", "size": size}
                )
            return results

    async def _generate_stability(
        self, prompt: str, api_key: str, size: str
    ) -> list[dict]:
        """Stability AI"""
        w, h = size.split("x")
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                self.PROVIDERS["stability"]["url"],
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "image/*",
                },
                files={"prompt": (None, prompt)},
                data={"aspect_ratio": f"{w}:{h}", "output_format": "png"},
            )
            resp.raise_for_status()

            filepath = (
                self.output_dir / f"stability_{int(datetime.now().timestamp())}.png"
            )
            with open(filepath, "wb") as f:
                f.write(resp.content)

            return [{"url": str(filepath), "provider": "stability", "size": size}]

    async def _generate_siliconflow(
        self, prompt: str, api_key: str, size: str, n: int
    ) -> list[dict]:
        """SiliconFlow (国产免费)"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                self.PROVIDERS["siliconflow"]["url"],
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "Kwai-Kolors/Kolors",
                    "prompt": prompt,
                    "image_size": size,
                    "num_images": n,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for i, item in enumerate(data.get("images", [])):
                url = item.get("url", "")
                if url:
                    img_resp = await client.get(url)
                    filepath = (
                        self.output_dir
                        / f"sf_{int(datetime.now().timestamp())}_{i}.png"
                    )
                    with open(filepath, "wb") as f:
                        f.write(img_resp.content)
                    results.append(
                        {"url": str(filepath), "provider": "siliconflow", "size": size}
                    )
            return results

    async def generate_cover_for_content(
        self,
        title: str,
        platform: str = "抖音",
        style: str = "现代简约",
    ) -> str:
        """为内容生成封面图"""
        # 平台尺寸
        sizes = {
            "抖音": "1024x1792",
            "小红书": "1024x1440",
            "B站": "1792x1024",
            "公众号": "1024x768",
            "YouTube": "1280x720",
            "TikTok": "1024x1792",
        }
        size = sizes.get(platform, "1024x1024")

        # 构建提示词
        style_prompts = {
            "现代简约": f"Minimalist modern cover for video titled '{title}', clean typography, vibrant gradient background, professional design",
            "复古": f"Vintage retro style cover for '{title}', classic colors, aged texture, nostalgic feel",
            "扁平化": f"Flat design illustration cover for '{title}', bold colors, geometric shapes, modern aesthetic",
            "手绘": f"Hand-drawn illustration cover for '{title}', watercolor style, artistic, personal touch",
            "科技感": f"Futuristic tech cover for '{title}', neon glow, dark background, circuit patterns, cyberpunk",
        }

        prompt = style_prompts.get(style, style_prompts["现代简约"])

        result = await self.generate(prompt, size=size)
        return result[0]["url"] if result else ""
