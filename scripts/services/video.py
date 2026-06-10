"""视频生成服务 - TTS + 字幕 + 封面"""

import asyncio
import json
import os
import subprocess
import tempfile
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont


class VideoGenerator:
    """视频生成器：TTS语音 + 字幕 + 封面"""

    VOICES = {
        "抖音": "zh-CN-YunxiNeural",
        "小红书": "zh-CN-XiaoxiaoNeural",
        "B站": "zh-CN-YunjianNeural",
        "公众号": "zh-CN-XiaoxiaoNeural",
        "YouTube": "zh-CN-YunxiNeural",
        "TikTok": "zh-CN-XiaoxiaoNeural",
    }

    def __init__(self, output_dir: str = "../data/videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_audio(
        self, text: str, platform: str = "抖音", output_path: str | None = None
    ) -> str:
        """生成 TTS 语音"""
        voice = self.VOICES.get(platform, "zh-CN-YunxiNeural")
        if not output_path:
            output_path = str(self.output_dir / "audio.mp3")

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return output_path

    def generate_subtitles(self, script: str, duration: int = 60) -> list[dict]:
        """从脚本生成字幕时间轴"""
        lines = [line.strip() for line in script.split("\n") if line.strip()]
        if not lines:
            return []

        # 过滤掉标记行
        content_lines = []
        for line in lines:
            if line.startswith("[") and line.endswith("]"):
                continue
            content_lines.append(line)

        if not content_lines:
            content_lines = lines

        # 平均分配时间
        time_per_line = duration / len(content_lines)
        subtitles = []
        current_time = 0

        for line in content_lines:
            minutes = int(current_time // 60)
            seconds = int(current_time % 60)
            subtitles.append(
                {
                    "time": f"{minutes:02d}:{seconds:02d}",
                    "text": line,
                    "duration": time_per_line,
                }
            )
            current_time += time_per_line

        return subtitles

    def generate_cover(
        self, title: str, platform: str = "抖音", output_path: str | None = None
    ) -> str:
        """生成封面图"""
        if not output_path:
            output_path = str(self.output_dir / "cover.png")

        # 平台尺寸
        sizes = {
            "抖音": (1080, 1920),
            "小红书": (1080, 1440),
            "B站": (1920, 1080),
            "公众号": (900, 500),
            "YouTube": (1280, 720),
            "TikTok": (1080, 1920),
        }
        width, height = sizes.get(platform, (1080, 1920))

        # 创建图片
        img = Image.new("RGB", (width, height), color=(15, 15, 15))
        draw = ImageDraw.Draw(img)

        # 尝试加载字体
        try:
            font = ImageFont.truetype("msyh.ttc", 72)
            small_font = ImageFont.truetype("msyh.ttc", 36)
        except (OSError, IOError):
            font = ImageFont.load_default()
            small_font = font

        # 绘制标题
        bbox = draw.textbbox((0, 0), title, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        draw.text((x, y), title, fill="white", font=font)

        # 绘制平台水印
        draw.text(
            (width - 200, height - 80),
            f"智媒圈 · {platform}",
            fill=(255, 165, 0),
            font=small_font,
        )

        img.save(output_path)
        return output_path

    def create_srt(self, subtitles: list[dict], output_path: str | None = None) -> str:
        """生成 SRT 字幕文件"""
        if not output_path:
            output_path = str(self.output_dir / "subtitles.srt")

        with open(output_path, "w", encoding="utf-8") as f:
            for i, sub in enumerate(subtitles, 1):
                start = sub["time"]
                duration = sub.get("duration", 3)
                # 计算结束时间
                parts = start.split(":")
                total_seconds = int(parts[0]) * 60 + int(parts[1])
                end_seconds = total_seconds + duration
                end = f"{int(end_seconds // 60):02d}:{int(end_seconds % 60):02d}"

                f.write(f"{i}\n")
                f.write(f"{start},000 --> {end},000\n")
                f.write(f"{sub['text']}\n\n")

        return output_path

    async def generate_video_package(
        self, script: str, title: str, platform: str = "抖音", duration: int = 60
    ) -> dict:
        """生成完整视频包（音频+字幕+封面）"""
        # 生成音频
        audio_path = await self.generate_audio(script, platform)

        # 生成字幕
        subtitles = self.generate_subtitles(script, duration)
        srt_path = self.create_srt(subtitles)

        # 生成封面
        cover_path = self.generate_cover(title, platform)

        return {
            "audio": audio_path,
            "subtitles": subtitles,
            "srt": srt_path,
            "cover": cover_path,
            "platform": platform,
            "duration": duration,
        }
