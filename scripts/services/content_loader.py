"""content/ 知识库加载器

为 prompts.py 提供方法论/平台模板/专家人设的加载能力：
- 按 Fire Score 维度（hook/trust/retention/conversion/emotion）匹配方法论
- 按平台中文名/别名匹配平台模板
- 按人设中文名/别名匹配专家人设
- 基于文件 mtime 缓存：编辑后自动失效，不增加 I/O
- 截断注入：单文件最多 800 字符，避免 prompt 过长
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


def _get_content_dir() -> Path:
    """运行时获取内容目录，支持环境变量动态覆盖"""
    return Path(
        os.environ.get(
            "ZHIMEIQUAN_CONTENT_DIR",
            str(Path(__file__).resolve().parents[2] / "content"),
        )
    )


# 向后兼容：允许通过 monkeypatch 直接修改 CONTENT_DIR
def _content_dir_default() -> Path:
    return _get_content_dir()


CONTENT_DIR = _content_dir_default()  # type: ignore[misc]


MAX_INJECT_CHARS = 800

METHODOLOGY_FILES: dict[str, str] = {
    "hook": "01-hook-power.md",
    "trust": "02-trust.md",
    "retention": "03-retention.md",
    "conversion": "04-conversion.md",
    "emotion": "05-emotion.md",
}

PLATFORM_ALIASES: dict[str, str] = {
    "抖音": "douyin",
    "douyin": "douyin",
    "小红书": "xiaohongshu",
    "xiaohongshu": "xiaohongshu",
    "redbook": "xiaohongshu",
    "B站": "bilibili",
    "b站": "bilibili",
    "bilibili": "bilibili",
    "bili": "bilibili",
    "公众号": "wechat",
    "wechat": "wechat",
    "微信公众号": "wechat",
    "YouTube": "youtube",
    "youtube": "youtube",
    "yt": "youtube",
    "TikTok": "tiktok",
    "tiktok": "tiktok",
    "抖音国际版": "tiktok",
    "快手": "kuaishou",
    "kuaishou": "kuaishou",
    "ks": "kuaishou",
    "视频号": "shipinhao",
    "shipinhao": "shipinhao",
    "微信视频号": "shipinhao",
    "wechat-channels": "shipinhao",
    "微博": "weibo",
    "weibo": "weibo",
    "新浪微博": "weibo",
    "知乎": "zhihu",
    "zhihu": "zhihu",
    "头条": "toutiao",
    "toutiao": "toutiao",
    "今日头条": "toutiao",
    "Instagram": "instagram",
    "instagram": "instagram",
    "ig": "instagram",
    "ins": "instagram",
    "X": "twitter",
    "Twitter": "twitter",
    "twitter": "twitter",
    "推特": "twitter",
    "x.com": "twitter",
}

PERSONA_ALIASES: dict[str, str] = {
    "学长型": "mentor",
    "mentor": "mentor",
    "学姐型": "sister",
    "sister": "sister",
    "专家型": "expert",
    "expert": "expert",
}


def _truncate(text: str, max_chars: int = MAX_INJECT_CHARS) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n...(已截断)"


@lru_cache(maxsize=64)
def _read_with_mtime(path_str: str, mtime_ns: int) -> str:
    return Path(path_str).read_text(encoding="utf-8")


def _read(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    # 使用纳秒级 mtime 以避免快速连续写入时缓存不失效
    stat = path.stat()
    return _read_with_mtime(str(path), stat.st_mtime_ns)


def _resolve_dir() -> Path:
    """解析实际的内容目录（优先 env var，其次 CONTENT_DIR）"""
    env_dir = os.environ.get("ZHIMEIQUAN_CONTENT_DIR")
    if env_dir:
        return Path(env_dir)
    if isinstance(CONTENT_DIR, Path):
        return CONTENT_DIR
    return _get_content_dir()


def clear_cache() -> None:
    """清空文件读取缓存（环境变量或文件变更后调用）"""
    _read_with_mtime.cache_clear()


def get_methodology(dimension: str) -> str:
    """读取 Fire Score 维度方法论。dimension ∈ {hook,trust,retention,conversion,emotion}"""
    fname = METHODOLOGY_FILES.get(dimension)
    if not fname:
        return ""
    return _truncate(_read(_resolve_dir() / "methodology" / fname))


def get_template(platform: str) -> str:
    """按平台名/别名读取平台爆款模板。未匹配返回空串。"""
    key = PLATFORM_ALIASES.get(platform, "")
    if not key:
        return ""
    return _truncate(_read(_resolve_dir() / "templates" / f"{key}-template.md"))


def get_persona(persona: str) -> str:
    """按人设名/别名读取专家人设指南。未匹配返回空串。"""
    key = PERSONA_ALIASES.get(persona, "")
    if not key:
        return ""
    return _truncate(_read(_resolve_dir() / "experts" / f"{key}-persona.md"))


def list_supported_platforms() -> list[str]:
    """返回所有支持的中文平台名（用于 API 校验/前端下拉）。"""
    return sorted(
        {k for k in PLATFORM_ALIASES if any("\u4e00" <= c <= "\u9fff" for c in k)}
    )


def list_supported_personas() -> list[str]:
    return sorted(
        {k for k in PERSONA_ALIASES if any("\u4e00" <= c <= "\u9fff" for c in k)}
    )


def clear_file_cache() -> None:
    """清空文件读取缓存（用于热更新/测试）"""
    _read_with_mtime.cache_clear()
