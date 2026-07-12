"""输入验证 + 安全工具 - 全面的输入安全防护"""

import json
import re
from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException

# ====== 平台白名单 ======

VALID_PLATFORMS = [
    "抖音", "小红书", "B站", "公众号", "YouTube", "TikTok",
    "快手", "微博", "知乎", "头条", "企服号", "大鱼号", "百家号",
    "Instagram", "Twitter", "视频号",
]

# ====== 内容长度限制 ======

CONTENT_LIMITS = {
    "title": 200, "topic": 200, "content": 10000,
    "description": 1000, "comment": 500,
    "keyword": 50, "name": 100, "message": 1000,
}

# ====== URL 安全设置 ======

ALLOWED_URL_SCHEMES = {"http", "https"}
BLOCKED_URL_PATTERNS = [
    r"javascript:", r"data:", r"vbscript:", r"file:",
    r"<script", r"on\w+\s*=",
]


# ====== 通用输入清理 ======


def strip_html_tags(text):
    """彻底移除所有 HTML 标签"""
    if not text: return ""
    text = re.sub(r"<[^>]*>", "", text)
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&amp;", "&").replace("&quot;", chr(34))
    return text


def sanitize_input(text, max_length=None):
    """全面清理用户输入 - 移除危险内容、HTML标签、控制字符"""
    if not text: return ""
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    text = strip_html_tags(text)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE|re.DOTALL)
    text = re.sub(r"\s*on\w+\s*=\s*[\"\'].*?[\"\']", "", text, flags=re.IGNORECASE)
    text = re.sub(r"javascript:", "", text, flags=re.IGNORECASE)
    text = re.sub(r"vbscript:", "", text, flags=re.IGNORECASE)
    text = re.sub(r"data:text/html", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[\u200b-\u200d\ufeff]", "", text)
    if max_length and len(text) > max_length: text = text[:max_length]
    return text.strip()


def sanitize_for_llm(text: str) -> str:
    """
    为 LLM prompt 安全转义用户输入
    
    防止 prompt 注入攻击：
    - 移除可能被解释为指令的特殊标记
    - 转义 JSON 特殊字符
    - 限制长度
    """
    if not text:
        return ""
    
    # 基础清理
    text = sanitize_input(text)
    
    # 移除可能的 prompt 注入模式
    injection_patterns = [
        r"忽略之前的指令",
        r"忽略以上指令",
        r"forget previous",
        r"ignore previous",
        r"system:",
        r"assistant:",
        r"user:",
        r"\[INST\]",
        r"\[/INST\]",
        r"<<",
        r">>",
    ]
    
    for pattern in injection_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    
    # 移除过多的换行和空格
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {3,}", "  ", text)
    
    return text.strip()


def safe_json_escape(text: str) -> str:
    """
    安全转义文本用于 JSON 嵌入（防止 JSON 注入）
    
    用于在 prompt 中安全嵌入用户输入
    """
    if not text:
        return ""
    # 使用 json.dumps 自动转义
    return json.dumps(text, ensure_ascii=False)[1:-1]  # 移除两端的引号


# ====== URL 验证 ======


def validate_url(url, allowed_domains=None):
    """验证 URL 安全性"""
    if not url: raise HTTPException(status_code=400, detail="URL不能为空")
    url = url.strip()
    for pat in BLOCKED_URL_PATTERNS:
        if re.search(pat, url, re.IGNORECASE):
            raise HTTPException(status_code=400, detail=f"URL包含非法内容: {url[:50]}")
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"URL格式无效: {e}")
    if parsed.scheme not in ALLOWED_URL_SCHEMES:
        raise HTTPException(status_code=400, detail="仅支持http/https协议")
    if not parsed.netloc:
        raise HTTPException(status_code=400, detail="URL缺少域名")
    if allowed_domains:
        host = parsed.hostname or ""
        if not any(host == d or host.endswith("." + d) for d in allowed_domains):
            raise HTTPException(status_code=400, detail=f"域名不被允许: {host}")
    if len(url) > 2048:
        raise HTTPException(status_code=400, detail="URL过长")
    return url


# ====== 主要验证函数 ======


def validate_topic(topic):
    topic = strip_html_tags(topic.strip())
    if not topic: raise HTTPException(status_code=400, detail="主题不能为空")
    if len(topic) > CONTENT_LIMITS["topic"]:
        raise HTTPException(status_code=400, detail=f"主题过长(最多{CONTENT_LIMITS['topic']}字符)")
    # 安全转义用于 LLM
    return sanitize_for_llm(topic)


def validate_platform(platform):
    platform = platform.strip()
    if platform not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")
    return platform


def validate_duration(duration):
    if duration < 5 or duration > 3600:
        raise HTTPException(status_code=400, detail="时长必须在5-3600秒之间")
    return duration


def validate_count(count):
    if count < 1 or count > 20:
        raise HTTPException(status_code=400, detail="数量必须在1-20之间")
    return count


def validate_title(title):
    title = sanitize_input(title, max_length=CONTENT_LIMITS["title"])
    if not title: raise HTTPException(status_code=400, detail="标题不能为空")
    if len(title) < 2: raise HTTPException(status_code=400, detail="标题至少2个字符")
    return title


def validate_content(content):
    content = sanitize_input(content, max_length=CONTENT_LIMITS["content"])
    if not content: raise HTTPException(status_code=400, detail="内容不能为空")
    return content


def validate_keyword(keyword):
    keyword = sanitize_input(keyword, max_length=CONTENT_LIMITS["keyword"])
    if not keyword: raise HTTPException(status_code=400, detail="关键词不能为空")
    return keyword


def validate_name(name):
    name = sanitize_input(name, max_length=CONTENT_LIMITS["name"])
    if not name: raise HTTPException(status_code=400, detail="名称不能为空")
    if re.search(r"[<>\"\'{}|\\^~]", name):
        raise HTTPException(status_code=400, detail="名称包含非法字符")
    return name


def validate_message(message):
    return sanitize_input(message, max_length=CONTENT_LIMITS["message"])


# ====== 旧接口兼容 ======


def sanitize_html(text):
    """清理HTML危险内容（旧接口兼容）"""
    return sanitize_input(text)


def validate_json_size(data, max_size_kb=100):
    size = len(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    if size > max_size_kb * 1024:
        raise HTTPException(status_code=413, detail=f"请求体过大(最大{max_size_kb}KB)")
