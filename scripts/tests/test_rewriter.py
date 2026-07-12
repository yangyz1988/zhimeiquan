"""内容改写引擎单元测试

覆盖: Content 数据模型、FireScore 评分模型、
ContentRewriter 核心改写逻辑、批量改写、跨平台适配、版本对比。
"""

import json
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from generators.rewriter import (
    Content,
    FireScore,
    ContentRewriter,
    PLATFORM_MAPPING,
    CROSS_PLATFORM_RULES,
)


# ── Content 模型 ──────────────────────────────────


class TestContent:
    def test_from_dict_full(self):
        data = {
            "title": "AI 入门指南",
            "body": "这是一篇关于 AI 的文章",
            "hook": "你知道 AI 有多强大吗？",
            "tags": ["AI", "入门"],
            "call_to_action": "点赞关注",
            "subtitles": [{"time": "0:00", "text": "介绍"}],
        }
        c = Content.from_dict(data)
        assert c.title == "AI 入门指南"
        assert c.body == "这是一篇关于 AI 的文章"
        assert c.hook == "你知道 AI 有多强大吗？"
        assert c.tags == ["AI", "入门"]
        assert c.call_to_action == "点赞关注"
        assert len(c.subtitles) == 1

    def test_from_dict_minimal(self):
        c = Content.from_dict({})
        assert c.title == ""
        assert c.body == ""
        assert c.hook == ""
        assert c.tags == []

    def test_from_dict_script_alias(self):
        """body 字段可以用 script 别名替代"""
        c = Content.from_dict({"script": "脚本内容"})
        assert c.body == "脚本内容"

    def test_to_dict(self):
        c = Content(title="标题", body="正文", hook="钩子", tags=["tag1"])
        d = c.to_dict()
        assert d["title"] == "标题"
        assert d["body"] == "正文"
        assert d["hook"] == "钩子"
        assert d["tags"] == ["tag1"]
        assert "call_to_action" not in d  # 空值被过滤

    def test_to_dict_empty(self):
        c = Content()
        d = c.to_dict()
        assert d == {}


# ── FireScore 模型 ────────────────────────────────


class TestFireScore:
    def test_from_dict_full(self):
        data = {
            "scores": {
                "hook": 85, "trust": 90, "retention": 80,
                "conversion": 75, "emotion": 88,
                "total": 84.5, "level": "Lv4 优秀",
                "suggestions": ["优化转化力"],
                "analysis": "整体表现良好",
            }
        }
        fs = FireScore.from_dict(data)
        assert fs.hook == 85
        assert fs.trust == 90
        assert fs.total == 84.5
        assert fs.level == "Lv4 优秀"
        assert fs.suggestions == ["优化转化力"]

    def test_from_dict_flat(self):
        """支持扁平格式（无 scores 包裹）"""
        data = {
            "hook": 80, "trust": 70, "retention": 90,
            "conversion": 60, "emotion": 85,
            "total": 77, "level": "Lv3 良好",
        }
        fs = FireScore.from_dict(data)
        assert fs.hook == 80
        assert fs.total == 77.0

    def test_from_dict_total_as_dict(self):
        """total 可能是嵌套字典"""
        data = {"scores": {"total": {"total": 90}}}
        fs = FireScore.from_dict(data)
        assert fs.total == 90.0

    def test_weak_dimensions(self):
        fs = FireScore(hook=70, trust=85, retention=60, conversion=90, emotion=50)
        weak = fs.weak_dimensions
        names = [n for n, _, _ in weak]
        assert "hook" in names
        assert "retention" in names
        assert "emotion" in names
        assert "trust" not in names
        assert "conversion" not in names

    def test_weak_dimensions_all_above_threshold(self):
        fs = FireScore(hook=85, trust=90, retention=85, conversion=85, emotion=85)
        assert fs.weak_dimensions == []

    def test_is_good_below_target(self):
        fs = FireScore(total=80)
        assert fs.is_good is False

    def test_is_good_at_target(self):
        fs = FireScore(total=95)
        assert fs.is_good is True

    def test_is_good_above_target(self):
        fs = FireScore(total=100)
        assert fs.is_good is True


# ── 平台映射 ──────────────────────────────────────


class TestPlatformMapping:
    def test_all_chinese_platforms_mapped(self):
        for cn_name in ["抖音", "小红书", "B站", "微博", "知乎", "公众号"]:
            assert cn_name in PLATFORM_MAPPING

    def test_all_english_platforms_present(self):
        for en in ["douyin", "xiaohongshu", "bilibili", "weibo", "zhihu", "wechat"]:
            assert en in PLATFORM_MAPPING.values()

    def test_cross_platform_rules_exist(self):
        assert len(CROSS_PLATFORM_RULES) > 0
        assert ("抖音", "小红书") in CROSS_PLATFORM_RULES
        assert ("B站", "抖音") in CROSS_PLATFORM_RULES


# ── ContentRewriter ───────────────────────────────


class TestContentRewriter:
    @pytest.fixture
    def rewriter(self):
        with patch("generators.rewriter.RuleScheduler"):
            return ContentRewriter(data_dir="/tmp/test_rules")

    def test_load_rules_returns_none_on_error(self, rewriter):
        result = rewriter._load_rules("未知平台")
        assert result is None

    def test_build_rewrite_system_prompt_with_weak_dims(self, rewriter):
        weak = [("hook", 45.0, 0.25), ("conversion", 50.0, 0.20)]
        prompt = rewriter._build_rewrite_system_prompt("抖音", weak, None)
        assert "你是智媒圈AI助手" in prompt
        assert "45.0" in prompt
        assert "50.0" in prompt
        assert "JSON格式" in prompt

    def test_build_rewrite_user_prompt(self, rewriter):
        content = Content(
            title="测试标题",
            body="测试正文",
            hook="测试钩子",
            tags=["AI", "科技"],
            call_to_action="点赞",
        )
        prompt = rewriter._build_rewrite_user_prompt(content)
        assert "测试标题" in prompt
        assert "测试正文" in prompt
        assert "AI 科技" in prompt

    def test_compare_versions_no_change(self):
        original = {"title": "A", "body": "B", "hook": "C", "tags": ["t1"]}
        rewritten = {"title": "A", "body": "B", "hook": "C", "tags": ["t1"]}
        result = ContentRewriter.compare_versions(original, rewritten)
        assert result["summary"] == "无变化"
        assert result["total_changes"] == 0

    def test_compare_versions_some_changes(self):
        original = {"title": "旧标题", "body": "旧正文", "hook": "旧钩子"}
        rewritten = {"title": "新标题", "body": "旧正文", "hook": "新钩子"}
        result = ContentRewriter.compare_versions(original, rewritten)
        assert result["total_changes"] == 2
        assert "title" in result["changed_fields"]
        assert "hook" in result["changed_fields"]
        assert "body" not in result["changed_fields"]

    def test_compare_versions_tags_diff(self):
        original = {"title": "A", "tags": ["t1", "t2"]}
        rewritten = {"title": "A", "tags": ["t2", "t3"]}
        result = ContentRewriter.compare_versions(original, rewritten)
        diff = result["diffs"]["tags"]
        assert diff["added"] == ["t3"]
        assert diff["removed"] == ["t1"]

    def test_compare_versions_length_tracking(self):
        original = {"title": "短", "body": "一段很短的文字"}
        rewritten = {"title": "这是一个更长的标题", "body": "一段非常长的文字内容"}
        result = ContentRewriter.compare_versions(original, rewritten)
        assert result["diffs"]["title"]["old_length"] == 1
        assert result["diffs"]["title"]["new_length"] == 9
        assert result["diffs"]["body"]["old_length"] == 7
        assert result["diffs"]["body"]["new_length"] == 11

    def test_get_stats(self, rewriter):
        stats = rewriter.get_stats()
        assert "total_rewrites" in stats
        assert "router_stats" in stats


# ── _log_rewrite 辅助函数 ─────────────────────────


class TestLogRewrite:
    def test_log_rewrite_creates_file(self, tmp_path):
        from generators.rewriter import _log_rewrite
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            _log_rewrite(
                content_id="test_001",
                platform="抖音",
                original_score=70.0,
                new_score=92.5,
                changes={"summary": "优化了标题和钩子"},
            )
            log_file = tmp_path / "data" / "rewrites" / "rewrite_test_001.json"
            assert log_file.exists()
            data = json.loads(log_file.read_text(encoding="utf-8"))
            assert data["content_id"] == "test_001"
            assert data["original_score"] == 70.0
            assert data["new_score"] == 92.5
            assert data["delta"] == 22.5
        finally:
            os.chdir(original_cwd)
