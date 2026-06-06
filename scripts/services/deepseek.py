import json
import os
from typing import AsyncIterator

import httpx

from services.cache import CacheService
from services.error_handler import retry
from services.logging import logger


class DeepSeekClient:
    def __init__(
        self, api_key: str | None = None, base_url: str = "https://api.deepseek.com"
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = base_url
        self.model = "deepseek-chat"
        self.cache = CacheService()

    @retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(httpx.HTTPError,))
    async def chat(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        use_cache: bool = True,
    ) -> str:
        # 生成缓存键
        cache_key = self.cache._make_key(
            "deepseek",
            {
                "prompt": prompt[:500],  # 截断避免过长
                "system": system[:200],
                "temperature": temperature,
            },
        )

        # 检查缓存
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                logger.info("DeepSeek 缓存命中", key=cache_key)
                return cached

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            result = resp.json()["choices"][0]["message"]["content"]

            # 缓存结果
            if use_cache:
                await self.cache.set(cache_key, result, ttl=3600)

            logger.info(
                "DeepSeek 调用成功",
                tokens_used=resp.json().get("usage", {}).get("total_tokens", 0),
            )
            return result

    @retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(httpx.HTTPError,))
    async def chat_stream(
        self, prompt: str, system: str = "", temperature: float = 0.7
    ) -> AsyncIterator[str]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        import json

                        data = json.loads(line[6:])
                        delta = data["choices"][0].get("delta", {})
                        if content := delta.get("content"):
                            yield content
