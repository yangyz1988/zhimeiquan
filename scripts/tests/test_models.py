"""模型路由测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.models import get_model, MODELS, BaseLLM, DeepSeekLLM, QwenLLM


def test_get_model_deepseek():
    model = get_model("deepseek")
    assert isinstance(model, DeepSeekLLM)
    assert model.model == "deepseek-chat"


def test_get_model_qwen():
    model = get_model("qwen")
    assert isinstance(model, QwenLLM)
    assert model.model == "qwen-turbo"


def test_get_model_invalid():
    with pytest.raises(ValueError, match="不支持的模型"):
        get_model("invalid_model")


def test_models_registry():
    assert "deepseek" in MODELS
    assert "qwen" in MODELS
    assert "ernie" in MODELS
    assert "hunyuan" in MODELS


@pytest.mark.asyncio
async def test_deepseek_chat_success():
    with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"}):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "测试响应"}}]
            }
            mock_response.raise_for_status = MagicMock()

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_response
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.__aexit__.return_value = None
            mock_client.return_value = mock_async_client

            client = DeepSeekLLM()
            result = await client.chat("test prompt")
            assert result == "测试响应"


def test_base_llm_abstract():
    """基类不能直接实例化"""
    with pytest.raises(TypeError):
        BaseLLM("key", "url", "model")
