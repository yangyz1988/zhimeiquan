"""内容调度服务 - 日历 + 定时发布"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from services.logging import logger


class ContentScheduler:
    """内容调度器"""

    def __init__(self, data_dir: str = "../data/scheduled"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.scheduler = AsyncIOScheduler()
        self.queue_file = self.data_dir / "queue.json"
        self.queue: list[dict] = self._load_queue()

    def _load_queue(self) -> list[dict]:
        """加载调度队列"""
        if not self.queue_file.exists():
            return []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_queue(self):
        """保存调度队列"""
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump(self.queue, f, ensure_ascii=False, indent=2)

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("内容调度器已启动")

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("内容调度器已停止")

    def schedule_post(
        self,
        project_id: str,
        content_id: str,
        platform: str,
        title: str,
        content: str,
        scheduled_at: datetime,
    ) -> dict:
        """调度一个内容发布"""
        job_id = f"{project_id}_{content_id}_{int(scheduled_at.timestamp())}"

        item = {
            "job_id": job_id,
            "project_id": project_id,
            "content_id": content_id,
            "platform": platform,
            "title": title,
            "content": content,
            "scheduled_at": scheduled_at.isoformat(),
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
        }

        self.queue.append(item)
        self._save_queue()

        # 添加到调度器
        self.scheduler.add_job(
            self._execute_post,
            "date",
            run_date=scheduled_at,
            args=[job_id],
            id=job_id,
        )

        logger.info(
            f"已调度发布任务: {title}",
            platform=platform,
            scheduled_at=scheduled_at.isoformat(),
        )

        return item

    def schedule_recurring(
        self,
        project_id: str,
        platform: str,
        title_template: str,
        cron: str,
    ) -> dict:
        """调度周期性发布（cron 表达式）"""
        # cron 格式: 分 时 日 月 周
        parts = cron.split()
        if len(parts) != 5:
            raise ValueError("cron 表达式必须为 5 部分")

        job_id = f"recurring_{project_id}_{platform}"

        item = {
            "job_id": job_id,
            "project_id": project_id,
            "platform": platform,
            "title_template": title_template,
            "cron": cron,
            "type": "recurring",
            "status": "scheduled",
        }

        self.queue.append(item)
        self._save_queue()

        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )
        self.scheduler.add_job(
            self._execute_recurring,
            trigger,
            args=[job_id],
            id=job_id,
        )

        logger.info(f"已调度周期任务: {title_template} ({cron})")
        return item

    async def _execute_post(self, job_id: str):
        """执行发布任务"""
        item = next((q for q in self.queue if q["job_id"] == job_id), None)
        if not item:
            return

        try:
            # 这里实际调用平台 API 发布
            logger.info(f"执行发布: {item['title']} -> {item['platform']}")
            item["status"] = "published"
            item["published_at"] = datetime.now().isoformat()
            self._save_queue()
        except Exception as e:
            item["status"] = "failed"
            item["error"] = str(e)
            self._save_queue()
            logger.error(f"发布失败: {item['title']} - {e}")

    async def _execute_recurring(self, job_id: str):
        """执行周期任务"""
        item = next((q for q in self.queue if q["job_id"] == job_id), None)
        if not item:
            return
        logger.info(f"周期任务触发: {item['title_template']}")

    def get_calendar(self, year: int, month: int) -> dict:
        """获取日历视图"""
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)

        items = [
            q
            for q in self.queue
            if q.get("scheduled_at")
            and start.isoformat() <= q["scheduled_at"] < end.isoformat()
        ]

        return {
            "year": year,
            "month": month,
            "items": items,
            "count": len(items),
        }

    def cancel_job(self, job_id: str) -> bool:
        """取消调度任务"""
        try:
            self.scheduler.remove_job(job_id)
            self.queue = [q for q in self.queue if q["job_id"] != job_id]
            self._save_queue()
            logger.info(f"已取消任务: {job_id}")
            return True
        except Exception:
            return False

    def get_queue(self) -> list[dict]:
        """获取调度队列"""
        return self.queue


# 全局实例
content_scheduler = ContentScheduler()
