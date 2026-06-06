import pytest
from services.prompts import Prompts


def test_generate_content_prompt():
    system, prompt = Prompts.generate_content("AI自媒体", "抖音", "学长型", 60)
    assert "抖音" in system
    assert "AI自媒体" in prompt
    assert "学长型" in prompt


def test_generate_content_with_rules():
    rules = {"title_rules": [{"rule": "标题包含数字"}]}
    system, prompt = Prompts.generate_content(
        "AI自媒体", "抖音", "学长型", 60, rules=rules
    )
    assert "爆款规则" in system


def test_generate_titles_prompt():
    system, prompt = Prompts.generate_titles("自媒体赚钱", "抖音", 5)
    assert "爆款标题" in system
    assert "自媒体赚钱" in prompt


def test_score_content_prompt():
    system, prompt = Prompts.score_content("标题", "正文内容", "抖音")
    assert "Fire Score" in system
    assert "标题" in prompt


def test_hook_patterns():
    from monitors.analyzer import RuleAnalyzer

    analyzer = RuleAnalyzer()
    titles = [{"title": "3个技巧让你涨粉10万"}, {"title": "没想到自媒体还能这样玩"}]
    result = analyzer.analyze_title_patterns(titles)
    assert "patterns" in result
    assert "hot_keywords" in result
