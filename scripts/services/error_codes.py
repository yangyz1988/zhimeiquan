"""统一错误码体系

提供标准化的错误码、错误消息和 HTTP 状态码映射。
所有 API 和内部服务应使用此错误码体系返回一致的错误信息。
"""

from typing import Any

from fastapi import HTTPException

ERROR_CODES: dict[str, tuple[str, int]] = {
    # Auth errors (AUTH-xxx)
    "AUTH001": ("未登录", 401),
    "AUTH002": ("API密钥无效", 403),
    "AUTH003": ("权限不足", 403),

    # Content errors (CONT-xxx)
    "CONT001": ("内容生成失败", 500),
    "CONT002": ("AI返回格式错误", 500),
    "CONT003": ("主题不能为空", 400),
    "CONT004": ("平台不支持", 400),

    # Rate limit errors (RATE-xxx)
    "RATE001": ("请求过于频繁", 429),

    # Service errors (SERV-xxx)
    "SERV001": ("服务暂时不可用", 503),
    "SERV002": ("API服务未启动", 503),

    # Data errors (DATA-xxx)
    "DATA001": ("记录不存在", 404),
    "DATA002": ("数据验证失败", 422),
}


class AppError(Exception):
    """应用级错误，包含错误码和元数据"""

    def __init__(self, code: str, message_override: str | None = None, metadata: dict | None = None):
        self.code = code
        self.message, self.status_code = ERROR_CODES.get(code, ("未知错误", 500))
        if message_override:
            self.message = message_override
        self.metadata = metadata or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "status_code": self.status_code,
            "metadata": self.metadata,
        }


def raise_error(code: str, message: str | None = None, metadata: dict | None = None):
    """抛出错误码对应的 HTTP 异常

    用法:
        raise_error("CONT003")  # 400: "主题不能为空"
        raise_error("AUTH002", "自定义消息")  # 403: "自定义消息"
    """
    error = AppError(code, message, metadata)
    raise HTTPException(
        status_code=error.status_code,
        detail=error.to_dict(),
    )


def get_error_detail(code: str) -> dict[str, Any]:
    """获取错误码详情"""
    msg, status = ERROR_CODES.get(code, ("未知错误", 500))
    return {
        "code": code,
        "message": msg,
        "status_code": status,
    }


def list_errors(category: str | None = None) -> list[dict[str, Any]]:
    """列出所有错误码，可按分类筛选（如 auth / cont / rate / serv / data）"""
    results = []
    for code, (message, status) in ERROR_CODES.items():
        if category and not code.lower().startswith(category.lower()):
            continue
        results.append({
            "code": code,
            "message": message,
            "status_code": status,
        })
    return results


def wrap_exception(e: Exception, code: str = "SERV001") -> AppError:
    """将普通异常包装为 AppError

    用法:
        try:
            ...
        except Exception as e:
            raise wrap_exception(e, "CONT001")
    """
    return AppError(code, message_override=str(e))
