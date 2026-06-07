"""模板服务测试"""

import pytest
import tempfile
from pathlib import Path
from services.templates import TemplateService


def test_template_service_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = TemplateService(templates_dir=tmpdir)
        # 应该自动创建默认模板
        templates = service.list_templates()
        assert len(templates) >= 4


def test_list_templates_filter_by_category():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = TemplateService(templates_dir=tmpdir)
        tutorials = service.list_templates(category="教程")
        assert all(t["category"] == "教程" for t in tutorials)


def test_list_templates_filter_by_platform():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = TemplateService(templates_dir=tmpdir)
        douyin = service.list_templates(platform="抖音")
        assert all(t.get("platform") in ["抖音", "通用"] for t in douyin)


def test_get_template_existing():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = TemplateService(templates_dir=tmpdir)
        template = service.get_template("tutorial_basic")
        assert template is not None
        assert template["name"] == "教程入门"


def test_get_template_nonexistent():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = TemplateService(templates_dir=tmpdir)
        assert service.get_template("nonexistent") is None


def test_save_template():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = TemplateService(templates_dir=tmpdir)
        new_template = {
            "id": "custom_test",
            "name": "测试模板",
            "category": "测试",
            "platform": "通用",
            "structure": [
                {"section": "intro", "duration": 5, "template": "你好{topic}"},
            ],
        }
        service.save_template(new_template)
        loaded = service.get_template("custom_test")
        assert loaded is not None
        assert loaded["name"] == "测试模板"


def test_apply_template():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = TemplateService(templates_dir=tmpdir)
        result = service.apply_template(
            "tutorial_basic",
            {
                "topic": "AI",
                "problem_point": "门槛高",
                "step1": "学基础",
                "step2": "做项目",
                "step3": "迭代",
                "result": "月入过万",
                "next_topic": "AI变现",
            },
        )
        assert "sections" in result
        assert any("AI" in s["content"] for s in result["sections"])
