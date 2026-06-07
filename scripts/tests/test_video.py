"""视频生成测试"""

import pytest
import os
import tempfile
from pathlib import Path
from services.video import VideoGenerator


def test_video_generator_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = VideoGenerator(output_dir=tmpdir)
        assert Path(tmpdir) == gen.output_dir
        assert Path(tmpdir).exists()


def test_generate_subtitles_basic():
    gen = VideoGenerator(output_dir=tempfile.mkdtemp())
    script = "第一句话。\n第二句话。\n第三句话。"
    subtitles = gen.generate_subtitles(script, duration=30)
    assert len(subtitles) == 3
    assert "time" in subtitles[0]
    assert "text" in subtitles[0]
    assert "duration" in subtitles[0]


def test_generate_subtitles_filters_markers():
    gen = VideoGenerator(output_dir=tempfile.mkdtemp())
    script = "[开场]\n第一句话。\n[结尾]\n第二句话。"
    subtitles = gen.generate_subtitles(script, duration=20)
    # 应该过滤掉方括号标记
    assert all("[" not in s["text"] for s in subtitles)
    assert len(subtitles) == 2


def test_generate_subtitles_empty():
    gen = VideoGenerator(output_dir=tempfile.mkdtemp())
    subtitles = gen.generate_subtitles("", duration=10)
    assert subtitles == []


def test_create_srt():
    gen = VideoGenerator(output_dir=tempfile.mkdtemp())
    subtitles = [
        {"time": "00:00", "text": "第一句", "duration": 3},
        {"time": "00:03", "text": "第二句", "duration": 3},
    ]
    srt_path = gen.create_srt(subtitles)
    assert Path(srt_path).exists()

    content = Path(srt_path).read_text(encoding="utf-8")
    assert "1\n" in content
    assert "00:00,000 --> 00:03,000" in content
    assert "第一句" in content


def test_generate_cover_creates_file():
    gen = VideoGenerator(output_dir=tempfile.mkdtemp())
    cover_path = gen.generate_cover("测试标题", platform="抖音")
    assert Path(cover_path).exists()
    assert cover_path.endswith(".png")

    # 清理
    os.remove(cover_path)


def test_voice_mapping():
    gen = VideoGenerator(output_dir=tempfile.mkdtemp())
    assert gen.VOICES["抖音"] == "zh-CN-YunxiNeural"
    assert gen.VOICES["小红书"] == "zh-CN-XiaoxiaoNeural"
