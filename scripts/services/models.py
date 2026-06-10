"""多模型 LLM 客户端 - 统一接口"""

import os
import time
from abc import ABC, abstractmethod

import httpx


class BaseLLM(ABC):
    """LLM 基类"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    @abstractmethod
    async def chat(
        self, prompt: str, system: str = "", temperature: float = 0.7
    ) -> str: ...


class DeepSeekLLM(BaseLLM):
    """DeepSeek API"""

    def __init__(self):
        super().__init__(
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            model="deepseek-chat",
        )

    async def chat(
        self, prompt: str, system: str = "", temperature: float = 0.7
    ) -> str:
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
            return resp.json()["choices"][0]["message"]["content"]


class QwenLLM(BaseLLM):
    """通义千问 API (阿里云)"""

    def __init__(self):
        super().__init__(
            api_key=os.getenv("QWEN_API_KEY", ""),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-turbo",
        )

    async def chat(
        self, prompt: str, system: str = "", temperature: float = 0.7
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]


class ERNIELLM(BaseLLM):
    """文心一言 API (百度)"""

    def __init__(self):
        self.api_key = os.getenv("ERNIE_API_KEY", "")
        self.secret_key = os.getenv("ERNIE_SECRET_KEY", "")
        self.model = "ernie-speed-128k"
        self._access_token: str | None = None
        self._token_expires_at: float = 0

    async def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://aip.baidubce.com/oauth/2.0/token",
                params={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.secret_key,
                },
            )
            resp.raise_for_status()
            self._access_token = resp.json()["access_token"]
            self._token_expires_at = time.time() + 25 * 24 * 3600
            return self._access_token

    async def chat(
        self, prompt: str, system: str = "", temperature: float = 0.7
    ) -> str:
        token = await self._get_access_token()
        messages = []
        if system:
            messages.append({"role": "user", "content": system + "\n\n" + prompt})
        else:
            messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{self.model}",
                params={"access_token": token},
                json={"messages": messages, "temperature": temperature},
            )
            resp.raise_for_status()
            return resp.json()["result"]


class HunyuanLLM(BaseLLM):
    """混元 API (腾讯)"""

    def __init__(self):
        super().__init__(
            api_key=os.getenv("HUNYUAN_API_KEY", ""),
            base_url="https://api.hunyuan.cloud.tencent.com/v1",
            model="hunyuan-standard",
        )

    async def chat(
        self, prompt: str, system: str = "", temperature: float = 0.7
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]


# 模型注册表
MODELS = {
    "deepseek": DeepSeekLLM,
    "qwen": QwenLLM,
    "ernie": ERNIELLM,
    "hunyuan": HunyuanLLM,
}


def get_model(name: str = "deepseek") -> BaseLLM:
    """获取模型实例"""
    cls = MODELS.get(name)
    if not cls:
        raise ValueError(f"不支持的模型: {name}")
    return cls()
