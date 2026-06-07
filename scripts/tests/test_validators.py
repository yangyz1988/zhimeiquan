"""验证器测试"""

import pytest
from fastapi import HTTPException
from services.validators import (
    validate_topic,
    validate_platform,
    validate_duration,
    validate_count,
    sanitize_html,
    validate_json_size,
)


def test_validate_topic_valid():
    assert validate_topic("AI 自媒体") == "AI 自媒体"


def test_validate_topic_empty():
    with pytest.raises(HTTPException) as exc:
        validate_topic("")
    assert exc.value.status_code == 400


def test_validate_topic_too_long():
    long_topic = "a" * 201
    with pytest.raises(HTTPException) as exc:
        validate_topic(long_topic)
    assert exc.value.status_code == 400


def test_validate_topic_xss():
    with pytest.raises(HTTPException) as exc:
        validate_topic("<script>alert('xss')</script>")
    assert exc.value.status_code == 400


def test_validate_platform_valid():
    assert validate_platform("抖音") == "抖音"
    assert validate_platform("小红书") == "小红书"


def test_validate_platform_invalid():
    with pytest.raises(HTTPException) as exc:
        validate_platform("FakePlatform")
    assert exc.value.status_code == 400


def test_validate_duration_valid():
    assert validate_duration(60) == 60
    assert validate_duration(5) == 5
    assert validate_duration(3600) == 3600


def test_validate_duration_too_short():
    with pytest.raises(HTTPException):
        validate_duration(3)


def test_validate_duration_too_long():
    with pytest.raises(HTTPException):
        validate_duration(4000)


def test_validate_count_valid():
    assert validate_count(1) == 1
    assert validate_count(20) == 20


def test_validate_count_out_of_range():
    with pytest.raises(HTTPException):
        validate_count(0)
    with pytest.raises(HTTPException):
        validate_count(25)


def test_sanitize_html_removes_script():
    dirty = "<p>正常</p><script>alert('xss')</script>"
    clean = sanitize_html(dirty)
    assert "<script>" not in clean
    assert "正常" in clean


def test_sanitize_html_removes_javascript():
    dirty = "<a href='javascript:alert(1)'>click</a>"
    clean = sanitize_html(dirty)
    assert "javascript:" not in clean


def test_sanitize_html_removes_onclick():
    dirty = "<div onclick='alert(1)'>click</div>"
    clean = sanitize_html(dirty)
    assert "onclick" not in clean.lower()


def test_validate_json_size_ok():
    data = {"key": "value"}
    validate_json_size(data, max_size_kb=100)  # 不应抛出


def test_validate_json_size_too_large():
    import pytest

    data = {"key": "x" * 200000}  # 200KB
    with pytest.raises(HTTPException) as exc:
        validate_json_size(data, max_size_kb=100)
    assert exc.value.status_code == 413
