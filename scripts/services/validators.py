"""输入验证 + 安全工具"""

import re
from typing import Any

from fastapi import HTTPException


def validate_topic(topic: str) -> str:
    """验证主题输入"""
    topic = topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="主题不能为空")
    if len(topic) > 200:
        raise HTTPException(status_code=400, detail="主题过长（最多 200 字符）")
    # 防止 XSS - 移除危险字符
    if re.search(r"<script|javascript:|on\w+\s*=", topic, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="主题包含非法字符")
    return topic


def validate_platform(platform: str) -> str:
    """验证平台"""
    valid_platforms = [
        "抖音",
        "小红书",
        "B站",
        "公众号",
        "YouTube",
        "TikTok",
        "快手",
        "微博",
        "知乎",
        "头条",
        "企鹅号",
        "大鱼号",
        "百家号",
    ]
    if platform not in valid_platforms:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")
    return platform


def validate_duration(duration: int) -> int:
    """验证时长"""
    if duration < 5 or duration > 3600:
        raise HTTPException(status_code=400, detail="时长必须在 5-3600 秒之间")
    return duration


def validate_count(count: int) -> int:
    """验证数量"""
    if count < 1 or count > 20:
        raise HTTPException(status_code=400, detail="数量必须在 1-20 之间")
    return count


def sanitize_html(text: str) -> str:
    """清理 HTML 危险内容"""
    if not text:
        return text
    # 移除 script 标签
    text = re.sub(
        r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL
    )
    # 移除 on* 事件
    text = re.sub(r"\s*on\w+\s*=\s*[\"'].*?[\"']", "", text, flags=re.IGNORECASE)
    # 移除 javascript: 协议
    text = re.sub(r"javascript:", "", text, flags=re.IGNORECASE)
    return text


def validate_json_size(data: Any, max_size_kb: int = 100) -> None:
    """验证 JSON 大小"""
    import json

    size = len(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    if size > max_size_kb * 1024:
        raise HTTPException(
            status_code=413, detail=f"请求体过大（最大 {max_size_kb}KB）"
        )
