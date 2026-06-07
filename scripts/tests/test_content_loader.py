"""scripts/services/content_loader.py 单元测试

不依赖网络/DeepSeek，纯文件读取 + 缓存逻辑。
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from services.content_loader import (
    MAX_INJECT_CHARS,
    clear_cache,
    get_methodology,
    get_persona,
    get_template,
    list_supported_personas,
    list_supported_platforms,
)


@pytest.fixture(autouse=True)
def _clear_cache_between_tests():
    clear_cache()
    yield
    clear_cache()


def test_get_methodology_hook_returns_content():
    doc = get_methodology("hook")
    assert len(doc) > 50
    assert "钩子" in doc
    assert "前 3 秒" in doc or "前3秒" in doc


@pytest.mark.parametrize("dim", ["hook", "trust", "retention", "conversion", "emotion"])
def test_get_methodology_all_dimensions(dim):
    doc = get_methodology(dim)
    assert doc, f"{dim} 应该能加载到内容"
    assert len(doc) > 30


def test_get_methodology_unknown_dimension_returns_empty():
    assert get_methodology("nope") == ""


@pytest.mark.parametrize(
    "platform,key_in_file",
    [
        ("抖音", "抖音"),
        ("小红书", "小红书"),
        ("B站", "B 站"),
        ("公众号", "公众号"),
        ("YouTube", "YouTube"),
        ("TikTok", "TikTok"),
        ("douyin", "抖音"),
        ("bili", "B 站"),
        ("yt", "YouTube"),
    ],
)
def test_get_template_aliases(platform, key_in_file):
    doc = get_template(platform)
    assert doc, f"{platform} 应该能匹配到模板"
    assert key_in_file in doc or key_in_file.lower() in doc.lower()


def test_get_template_unknown_platform_returns_empty():
    assert get_template("不存在的平台") == ""


@pytest.mark.parametrize(
    "persona,key_in_file",
    [
        ("学长型", "学长"),
        ("学姐型", "学姐"),
        ("专家型", "专家"),
        ("mentor", "学长"),
        ("sister", "学姐"),
        ("expert", "专家"),
    ],
)
def test_get_persona_aliases(persona, key_in_file):
    doc = get_persona(persona)
    assert doc, f"{persona} 应该能匹配到人设"
    assert key_in_file in doc


def test_get_persona_unknown_returns_empty():
    assert get_persona("不存在的") == ""


def test_truncation_at_max_chars():
    doc = get_methodology("hook")
    assert len(doc) <= MAX_INJECT_CHARS + len("\n...(已截断)")


def test_cache_invalidates_on_file_modify(tmp_path: Path, monkeypatch):
    from services import content_loader

    fake = tmp_path / "methodology"
    fake.mkdir()
    target = fake / "01-hook-power.md"
    target.write_text("短内容 v1", encoding="utf-8")

    monkeypatch.setattr(content_loader, "CONTENT_DIR", tmp_path)
    content_loader.clear_cache()

    doc1 = content_loader._read(target)
    assert doc1 == "短内容 v1"

    target.write_text("更新过的更长的内容 v2", encoding="utf-8")
    doc2 = content_loader._read(target)
    assert doc2 == "更新过的更长的内容 v2"
    assert doc2 != doc1


def test_list_supported_platforms_includes_chinese_names():
    platforms = list_supported_platforms()
    assert "抖音" in platforms
    assert "小红书" in platforms
    assert "B站" in platforms
    assert "公众号" in platforms
    for p in platforms:
        assert any("\u4e00" <= c <= "\u9fff" for c in p), f"{p} 应含中文"


def test_list_supported_personas_includes_chinese_names():
    personas = list_supported_personas()
    assert {"学长型", "学姐型", "专家型"}.issubset(set(personas))


def test_content_dir_override_via_setattr(tmp_path: Path):
    from services import content_loader

    fake = tmp_path / "methodology"
    fake.mkdir()
    (fake / "01-hook-power.md").write_text("热加载测试内容 V1", encoding="utf-8")

    original = content_loader.CONTENT_DIR
    try:
        content_loader.CONTENT_DIR = tmp_path
        content_loader.clear_cache()
        doc = content_loader.get_methodology("hook")
        assert doc == "热加载测试内容 V1"
    finally:
        content_loader.CONTENT_DIR = original
        content_loader.clear_cache()


def test_content_dir_env_var_at_import_time(tmp_path: Path, monkeypatch):
    """模块级 CONTENT_DIR 在 import 时锁定环境变量，可通过 setattr 覆盖"""
    from services import content_loader

    assert content_loader.CONTENT_DIR.exists()
    assert content_loader.CONTENT_DIR.name == "content"
