"""数据清洗管道测试

测试 HotContentParser 的解析、分词、钩子识别功能。
"""

import pytest


# ================================================
# HotContentParser 测试
# ================================================

class TestHotContentParser:
    """HotContentParser 单元测试"""

    def test_extract_titles_from_list_of_dicts(self):
        """从 dict 列表提取标题"""
        from monitors.parser import HotContentParser

        raw = [
            {"title": "测试标题1"},
            {"title": "测试标题2"},
            {"word": "热搜词"},
        ]
        titles = HotContentParser._extract_titles(raw)
        assert "测试标题1" in titles
        assert "测试标题2" in titles
        assert "热搜词" in titles

    def test_extract_titles_from_list_of_strings(self):
        """从字符串列表提取标题"""
        from monitors.parser import HotContentParser

        raw = ["标题A", "标题B", "标题C"]
        titles = HotContentParser._extract_titles(raw)
        assert len(titles) == 3

    def test_extract_titles_deduplication(self):
        """去重测试"""
        from monitors.parser import HotContentParser

        raw = ["标题A", "标题A", "标题B"]
        titles = HotContentParser._extract_titles(raw)
        assert titles == ["标题A", "标题B"] or len(titles) == 2

    def test_clean_pipeline_html_removal(self):
        """HTML 标签清洗"""
        from monitors.parser import HotContentParser

        dirty = ["<em>热点</em>话题", "正常标题"]
        cleaned = HotContentParser._clean(dirty)
        assert all("<" not in t for t in cleaned)

    def test_clean_pipeline_short_filter(self):
        """短标题过滤"""
        from monitors.parser import HotContentParser

        dirty = ["A", "正常标题", "", " "]
        cleaned = HotContentParser._clean(dirty)
        assert "A" not in cleaned
        assert "" not in cleaned
        assert "正常标题" in cleaned

    def test_clean_pipeline_long_filter(self):
        """过长的标题过滤"""
        from monitors.parser import HotContentParser

        long_title = "A" * 300
        dirty = [long_title, "正常标题"]
        cleaned = HotContentParser._clean(dirty)
        assert long_title not in cleaned or len(cleaned) == 1

    def test_clean_pipeline_url_filter(self):
        """URL 过滤"""
        from monitors.parser import HotContentParser

        dirty = ["https://example.com/some-path", "正常标题"]
        cleaned = HotContentParser._clean(dirty)
        assert "https://example.com/some-path" not in cleaned or len([t for t in cleaned if t.startswith("http")]) == 0

    def test_clean_pipeline_dedup_case_insensitive(self):
        """大小写不敏感去重"""
        from monitors.parser import HotContentParser

        dirty = ["Test Title", "test title", "TEST TITLE"]
        cleaned = HotContentParser._clean(dirty)
        assert len(cleaned) == 1

    def test_extract_hook_patterns(self):
        """钩子类型识别"""
        from monitors.parser import HotContentParser

        titles = [
            "3个技巧让你涨粉10万",
            "没想到自媒体还能这样玩",
            "怎么办？流量一直上不去",
            "赚钱秘籍大公开",
            "震惊！这个App太强了",
        ]
        hooks = HotContentParser.extract_hook_patterns(titles)
        assert len(hooks) > 0
        # 数字型应该被识别
        digital = [h for h in hooks if h["type"] == "数字型"]
        assert len(digital) > 0
        assert digital[0]["count"] >= 1

    def test_extract_topics_chinese(self):
        """中文话题提取"""
        from monitors.parser import HotContentParser

        titles = [
            "AI工具让工作效率翻倍",
            "自媒体赚钱AI工具推荐",
            "职场生存指南2026",
            "副业赚钱新思路",
            "职场穿搭分享",
        ]
        topics = HotContentParser.extract_topics(titles)
        assert isinstance(topics, list)
        # 应该有至少几个话题词
        assert len(topics) > 0

    def test_compute_stats(self):
        """统计摘要计算"""
        from monitors.parser import HotContentParser

        titles = ["标题1", "标题22", "标题333"]
        hooks = HotContentParser.extract_hook_patterns(titles)
        stats = HotContentParser._compute_stats(titles, hooks)
        assert stats["total_items"] == 3
        assert stats["avg_title_length"] > 0
        assert stats["min_length"] == 3
        assert stats["max_length"] == 4

    def test_build_result(self):
        """快捷构建测试"""
        from monitors.parser import HotContentParser

        titles = ["测试标题1", "测试标题2", "测试标题3"]
        result = HotContentParser._build_result(titles)
        assert "titles" in result
        assert "topics" in result
        assert "hook_patterns" in result
        assert "stats" in result
        assert result["stats"]["total_items"] == 3

    def test_generic_parse(self):
        """通用解析器兜底测试"""
        from monitors.parser import HotContentParser

        raw = [{"title": "A"}, {"title": "B"}]
        result = HotContentParser._generic_parse(raw)
        assert len(result["titles"]) >= 1

    def test_parse_with_unknown_platform(self):
        """未知平台的解析"""
        from monitors.parser import HotContentParser

        raw = [{"title": "测试内容"}]
        result = HotContentParser.parse("不存在的平台", raw)
        assert "titles" in result
        assert "测试内容" in result["titles"]


# ================================================
# 跨平台热点测试
# ================================================

class TestCrossPlatformTopics:
    """跨平台热点发现测试"""

    def test_cross_platform_detection(self):
        from monitors.parser import HotContentParser

        platform_results = {
            "抖音": ["AI工具", "副业赚钱", "职场"],
            "B站": ["AI工具", "学习技巧"],
            "小红书": ["AI工具", "穿搭", "护肤"],
        }
        cross = HotContentParser.get_cross_platform_topics(platform_results)
        # AI工具 出现在 3 个平台，应该被检测到
        ai_tool = [c for c in cross if c["topic"] == "AI工具"]
        assert len(ai_tool) > 0
        assert ai_tool[0]["platform_count"] == 3

    def test_cross_platform_min_threshold(self):
        from monitors.parser import HotContentParser

        platform_results = {
            "抖音": ["独家话题"],
            "B站": ["另一话题"],
        }
        cross = HotContentParser.get_cross_platform_topics(platform_results, min_platforms=2)
        assert len(cross) == 0  # 没有话题出现在 >=2 个平台


# ================================================
# Hook 模式正则测试
# ================================================

class TestHookPatterns:
    """钩子正则测试"""

    def test_number_hook(self):
        import re
        pattern = r"\d+"
        assert re.search(pattern, "3个方法")
        assert re.search(pattern, "10大技巧")
        assert not re.search(pattern, "方法")

    def test_counter_intuitive_hook(self):
        import re
        pattern = r"(竟然|没想到|原来|居然|真的|不为人知|揭秘|真相)"
        assert re.search(pattern, "没想到是这个结果")
        assert re.search(pattern, "揭秘行业内幕")
        assert not re.search(pattern, "普通标题")

    def test_pain_point_hook(self):
        import re
        pattern = r"(怎么办|如何|怎么|为什么|解决|摆脱|不再|告别)"
        assert re.search(pattern, "怎么办流量上不去")
        assert re.search(pattern, "如何提高效率")
        assert re.search(pattern, "告别拖延症")
        assert not re.search(pattern, "今天天气不错")

    def test_emotion_hook(self):
        import re
        pattern = r"(气死|震惊|无语|绝了|离谱|炸裂|泪目|笑死|哭死)"
        assert re.search(pattern, "震惊！这件事太炸裂了")
        assert re.search(pattern, "笑死了哈哈")
        assert not re.search(pattern, "正常内容")
