"""自主 Agent - 自动发布机器人"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from services.logging import logger
from services.data_loop import DataTracker
from services.video import VideoGenerator
from services.scheduler_service import content_scheduler


class AutonomousAgent:
    """自主 Agent - 自动生成 + 调度 + 发布 + 数据回流"""

    def __init__(self, data_dir: str = "../data/agents"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tracker = DataTracker()
        self.video = VideoGenerator()
        self.queue_file = self.data_dir / "queue.json"
        self.log_file = self.data_dir / "activity.log"

    def create_auto_publish_task(
        self,
        project_id: str,
        platform: str,
        topic: str,
        frequency: str = "daily",
        time_of_day: str = "10:00",
    ) -> dict:
        """创建自动发布任务"""
        task = {
            "task_id": f"auto_{project_id}_{int(datetime.now().timestamp())}",
            "project_id": project_id,
            "platform": platform,
            "topic": topic,
            "frequency": frequency,
            "time_of_day": time_of_day,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "stats": {
                "total_published": 0,
                "total_views": 0,
                "avg_engagement": 0,
            },
        }

        tasks = self._load_tasks()
        tasks.append(task)
        self._save_tasks(tasks)

        # 添加到调度器
        hour, minute = time_of_day.split(":")
        if frequency == "daily":
            cron = f"{minute} {hour} * * *"
        elif frequency == "weekly":
            cron = f"{minute} {hour} * * 1"
        else:
            cron = f"{minute} {hour} * * *"

        content_scheduler.schedule_recurring(
            project_id,
            platform,
            f"Auto: {topic}",
            cron,
        )

        self._log_activity(
            f"创建自动任务: {topic} ({platform}, {frequency} {time_of_day})"
        )
        return task

    def _load_tasks(self) -> list[dict]:
        if not self.queue_file.exists():
            return []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_tasks(self, tasks: list[dict]):
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

    def _log_activity(self, message: str):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")
        logger.info(f"Agent: {message}")

    def get_tasks(self) -> list[dict]:
        """获取所有自动任务"""
        return self._load_tasks()

    def get_activity_log(self, limit: int = 100) -> list[str]:
        """获取活动日志"""
        if not self.log_file.exists():
            return []
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines[-limit:]


# 全局实例
autonomous_agent = AutonomousAgent()
