"""
Clerk JWT 鉴权服务
支持两种验证模式：
1. PEM 公钥本地验证（生产环境推荐，性能好）
2. JWKS 远程公钥验证（开发环境方便）
"""

import os
import time
from typing import Optional, Dict, Any
from functools import lru_cache

import jwt
from jwt import PyJWKClient

from services.logging import logger
from services.error_handler import ServiceError


class AuthError(ServiceError):
    """认证错误"""
    def __init__(self, message: str = "未授权访问", code: str = "unauthorized"):
        super().__init__(message, code=code, status=401)


class ClerkAuth:
    """Clerk JWT 鉴权"""

    def __init__(self):
        self.issuer = os.getenv("CLERK_JWT_ISSUER", "")
        self.audience = os.getenv("CLERK_JWT_AUDIENCE", "")
        self.pem_key = os.getenv("CLERK_JWT_VERIFICATION_KEY", "")
        self.jwks_url = os.getenv("CLERK_JWKS_URL", "")
        self.enabled = bool(os.getenv("CLERK_SECRET_KEY") or self.pem_key or self.jwks_url)

        # 如果没有配置 JWKS URL，从 issuer 推导
        if not self.jwks_url and self.issuer:
            self.jwks_url = f"{self.issuer}/.well-known/jwks.json"

        self._jwks_client = None
        self._public_key = None

        if not self.enabled:
            logger.warning("Clerk 鉴权未启用（缺少配置），API 将处于开放状态")

    def _get_jwks_client(self) -> PyJWKClient:
        """获取 JWKS 客户端（懒加载）"""
        if not self._jwks_client:
            if not self.jwks_url:
                raise AuthError("JWKS URL 未配置")
            self._jwks_client = PyJWKClient(self.jwks_url)
        return self._jwks_client

    def _get_signing_key(self, token: str) -> Any:
        """获取签名公钥"""
        # 优先使用本地 PEM 公钥
        if self.pem_key:
            return self.pem_key

        # 其次使用 JWKS 远程获取
        if self.jwks_url:
            client = self._get_jwks_client()
            return client.get_signing_key_from_jwt(token).key

        raise AuthError("未配置任何验证密钥")

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        验证 JWT Token
        返回解码后的 payload
        """
        if not self.enabled:
            # 开发模式：返回 mock 用户
            logger.debug("鉴权未启用，使用 mock 用户")
            return {
                "sub": "dev_mock_user",
                "userId": "dev_mock_user",
                "email": "dev@local.test",
                "org_id": None,
            }

        if not token:
            raise AuthError("缺少 Authorization Token")

        # 去除 Bearer 前缀
        if token.lower().startswith("bearer "):
            token = token[7:]

        try:
            signing_key = self._get_signing_key(token)

            options = {
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": bool(self.issuer),
                "verify_aud": bool(self.audience),
            }

            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                issuer=self.issuer if self.issuer else None,
                audience=self.audience if self.audience else None,
                options=options,
            )

            # 标准化字段
            payload["userId"] = payload.get("sub", "")
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError("Token 已过期", code="token_expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT 验证失败: {str(e)}")
            raise AuthError("无效的 Token", code="invalid_token")
        except Exception as e:
            logger.error(f"鉴权异常: {str(e)}")
            raise AuthError("鉴权服务异常", code="auth_error")

    def get_user_id(self, token: str) -> str:
        """从 token 中提取 userId"""
        payload = self.verify_token(token)
        return payload.get("userId", "")


# 全局单例
auth_service = ClerkAuth()


def get_current_user_id(authorization: Optional[str]) -> str:
    """便捷函数：获取当前用户 ID"""
    return auth_service.get_user_id(authorization or "")
