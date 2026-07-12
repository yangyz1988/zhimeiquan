"""自主 Agent - 自动发布机器人 + 矩阵发布"""

import json
from collections import defaultdict
from datetime import datetime

from services.logging import logger
from pathlib import Path

from services.logging import logger
from services.data_loop import DataTracker
from services.video import VideoGenerator
from services.scheduler_service import content_scheduler


class AutonomousAgent:
    """自主 Agent - 自动生成 + 调度 + 发布 + 数据回流 + 矩阵管理"""

    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir or "../data/agents")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.matrix_dir = self.data_dir / "matrix"
        self.matrix_dir.mkdir(parents=True, exist_ok=True)
        self.tracker = DataTracker()
        self.video = VideoGenerator()
        self.queue_file = self.data_dir / "queue.json"
        self.log_file = self.data_dir / "activity.log"

    def create_auto_publish_task(self, project_id, platform, topic, frequency="daily", time_of_day="10:00"):
        task = {
            "task_id": f"auto_{project_id}_{int(datetime.now().timestamp())}",
            "project_id": project_id, "platform": platform, "topic": topic,
            "frequency": frequency, "time_of_day": time_of_day,
            "status": "active", "created_at": datetime.now().isoformat(),
            "stats": {"total_published": 0, "total_views": 0, "avg_engagement": 0},
        }
        tasks = self._load_tasks()
        tasks.append(task)
        self._save_tasks(tasks)
        hour, minute = time_of_day.split(":")
        cron = f"{minute} {hour} * * *"
        if frequency == "weekly": cron = f"{minute} {hour} * * 1"
        content_scheduler.schedule_recurring(project_id, platform, f"Auto: {topic}", cron)
        self._log_activity(f"创建自动任务: {topic} ({platform}, {frequency} {time_of_day})")
        return task

    def _load_tasks(self):
        if not self.queue_file.exists(): return []
        with open(self.queue_file, "r", encoding="utf-8") as f: return json.load(f)

    def _save_tasks(self, tasks):
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

    def _log_activity(self, message):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")
        logger.info(f"Agent: {message}")

    def get_tasks(self):
        return self._load_tasks()

    def get_activity_log(self, limit=100):
        if not self.log_file.exists(): return []
        with open(self.log_file, "r", encoding="utf-8") as f:
            return f.readlines()[-limit:]

    # ====== Moat 5: 矩阵发布 ======

    def create_matrix_task(self, project_id, platforms, topic, frequency="daily"):
        task_id = f"matrix_{project_id}_{int(datetime.now().timestamp())}"
        ptasks = [{"platform": p, "status": "active",
                   "total_published": 0, "total_views": 0, "total_engagement": 0}
                  for p in platforms]
        mt = {"task_id": task_id, "project_id": project_id, "topic": topic,
              "frequency": frequency, "platforms": platforms,
              "platform_tasks": ptasks, "status": "active",
              "created_at": datetime.now().isoformat(),
              "updated_at": datetime.now().isoformat(),
              "stats": {"total_published": 0, "total_views": 0, "total_likes": 0,
                       "total_comments": 0, "total_shares": 0, "avg_engagement_rate": 0}}
        with open(self.matrix_dir / f"{task_id}.json", "w", encoding="utf-8") as f:
            json.dump(mt, f, ensure_ascii=False, indent=2)
        for p in platforms:
            cron = "0 10 * * *"
            if frequency == "weekly": cron = "0 10 * * 1"
            content_scheduler.schedule_recurring(f"{project_id}_{p}", p, f"Matrix: {topic}", cron)
        self._log_activity(f"创建矩阵任务: {topic} ({len(platforms)} 平台, {frequency})")
        return mt

    def get_matrix_stats(self, project_id):
        mts = []
        for f in self.matrix_dir.glob(f"matrix_{project_id}_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    mts.append(json.load(fh))
            except Exception as e:
                logger.exception(f"加载矩阵任务失败 {f.name}")
        if not mts:
            return {"project_id": project_id, "exists": False, "message": "未找到矩阵任务"}
        ad = Path("../data/analytics")
        ps = defaultdict(lambda: {"total_content": 0, "total_views": 0, "total_likes": 0,
                                     "total_comments": 0, "total_shares": 0})
        for f in ad.glob(f"{project_id}_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    r = json.load(fh)
                p = r.get("platform", "未知")
                m = r.get("metrics", {})
                ps[p]["total_content"] += 1
                ps[p]["total_views"] += m.get("views", 0)
                ps[p]["total_likes"] += m.get("likes", 0)
                ps[p]["total_comments"] += m.get("comments", 0)
                ps[p]["total_shares"] += m.get("shares", 0)
            except (json.JSONDecodeError, KeyError, OSError) as e:
                logger.warning(f"解析分析记录失败 {f.name}", error=str(e))
        tv = sum(d["total_views"] for d in ps.values())
        te = sum(d["total_likes"]+d["total_comments"]+d["total_shares"] for d in ps.values())
        pr = [{"platform": p, "total_content": d["total_content"],
               "total_views": d["total_views"],
               "avg_engagement_rate": round((d["total_likes"]+d["total_comments"]+d["total_shares"])/max(d["total_views"],1)*100, 2)}
              for p, d in ps.items()]
        pr.sort(key=lambda x: x["avg_engagement_rate"], reverse=True)
        return {"project_id": project_id, "exists": True, "matrix_tasks": len(mts),
                "total_platforms": len(ps), "total_views": tv, "total_engagement": te,
                "avg_engagement_rate": round(te/max(tv,1), 4),
                "platform_ranking": pr, "best_platform": pr[0] if pr else None,
                "generated_at": datetime.now().isoformat()}

    def auto_optimize(self, project_id):
        stats = self.get_matrix_stats(project_id)
        if not stats.get("exists"):
            return {"project_id": project_id, "status": "no_data", "optimizations": []}
        opts = []
        if stats.get("platform_ranking") and len(stats["platform_ranking"]) >= 2:
            best = stats["platform_ranking"][0]
            worst = stats["platform_ranking"][-1]
            if best["avg_engagement_rate"] > worst["avg_engagement_rate"] * 2:
                opts.append({"type": "platform_focus",
                            "action": f"增加在 {best['platform']} 的发布频率",
                            "priority": "high"})
        if stats["total_views"] < 1000:
            opts.append({"type": "volume", "action": "增加内容发布量", "priority": "medium"})
        if stats.get("avg_engagement_rate", 0) < 0.03:
            opts.append({"type": "engagement", "action": "优化内容钩子和CTA", "priority": "high"})
        result = {"project_id": project_id, "status": "optimized",
                 "current_stats": {"total_views": stats["total_views"],
                                  "avg_engagement_rate": stats["avg_engagement_rate"]},
                 "optimizations": opts,
                 "generated_at": datetime.now().isoformat()}
        with open(self.matrix_dir / f"optimize_{project_id}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        self._log_activity(f"矩阵优化完成: {project_id}, {len(opts)} 条建议")
        return result

    def schedule_auto_publish(self):
        now = datetime.now()
        triggered = []
        errors = []
        for f in self.matrix_dir.glob("matrix_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    task = json.load(fh)
            except Exception as e:
                logger.exception(f"读取矩阵任务失败 {f.name}")
                errors.append({"file": f.name, "error": str(e)})
                continue
            if task.get("status") != "active": continue
            updated_at = task.get("updated_at", "")
            if updated_at:
                try:
                    last = datetime.fromisoformat(updated_at)
                    freq = task.get("frequency", "daily")
                    if freq == "daily" and (now-last).total_seconds() < 82800: continue
                    if freq == "weekly" and (now-last).total_seconds() < 604800: continue
                except (ValueError, TypeError) as e:
                    logger.warning(f"解析任务日期失败", task=f.name, error=str(e))
            for pt in task.get("platform_tasks", []):
                if pt.get("status") == "active":
                    pt["total_published"] = pt.get("total_published", 0) + 1
            task["updated_at"] = now.isoformat()
            task["stats"]["total_published"] = task["stats"].get("total_published", 0) + 1
            try:
                with open(f, "w", encoding="utf-8") as fh:
                    json.dump(task, fh, ensure_ascii=False, indent=2)
                triggered.append({"task_id": task["task_id"],
                                 "topic": task.get("topic", ""),
                                 "platforms": task.get("platforms", [])})
            except Exception as e:
                logger.exception(f"触发矩阵任务失败 {f.name}")
                errors.append({"file": f.name, "error": str(e)})
        self._log_activity(f"自动发布检查完成: 触发 {len(triggered)} 个任务")
        return {"status": "completed", "triggered_count": len(triggered),
                "error_count": len(errors), "triggered_tasks": triggered,
                "errors": errors, "checked_at": now.isoformat()}


# 全局实例
autonomous_agent = AutonomousAgent()
