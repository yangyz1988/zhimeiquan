"""后端监控服务 - 数据库连接池 + 任务监控 + 告警通知"""

import asyncio
import os
import threading
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional

from services.logging import logger
from services.metrics import metrics


class DatabaseMonitor:
    """数据库连接池监控"""

    def __init__(self):
        self._lock = threading.Lock()
        self._connections: Dict[int, dict] = {}
        self._connection_id = 0
        self._total_connections = 0
        self._max_connections = 0
        self._connection_errors = 0

    def track_connection(self, pool_name: str = "default") -> int:
        """追踪新连接"""
        with self._lock:
            self._connection_id += 1
            conn_id = self._connection_id
            self._connections[conn_id] = {
                "id": conn_id,
                "pool_name": pool_name,
                "created_at": datetime.now(),
                "status": "active",
            }
            self._total_connections += 1
            self._max_connections = max(self._max_connections, len(self._connections))
        return conn_id

    def release_connection(self, conn_id: int):
        """释放连接"""
        with self._lock:
            if conn_id in self._connections:
                self._connections[conn_id]["status"] = "released"
                self._connections[conn_id]["released_at"] = datetime.now()
                del self._connections[conn_id]

    def record_error(self):
        """记录连接错误"""
        with self._lock:
            self._connection_errors += 1

    def get_stats(self) -> dict:
        """获取连接池统计"""
        with self._lock:
            active = len(self._connections)
            return {
                "active_connections": active,
                "total_connections": self._total_connections,
                "max_connections": self._max_connections,
                "connection_errors": self._connection_errors,
                "pool_status": "healthy" if active < 10 else ("warning" if active < 20 else "critical"),
            }


class TaskMonitor:
    """异步任务监控"""

    def __init__(self):
        self._lock = threading.Lock()
        self._tasks: Dict[str, dict] = {}
        self._task_stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "running": 0,
        }

    def start_task(self, task_id: str, task_name: str, **kwargs):
        """标记任务开始"""
        with self._lock:
            self._tasks[task_id] = {
                "task_id": task_id,
                "task_name": task_name,
                "status": "running",
                "start_time": datetime.now(),
                "kwargs": kwargs,
            }
            self._task_stats["total"] += 1
            self._task_stats["running"] += 1

    def complete_task(self, task_id: str, success: bool = True, error: str = ""):
        """标记任务完成"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = "success" if success else "failed"
                self._tasks[task_id]["end_time"] = datetime.now()
                self._tasks[task_id]["duration"] = (
                    self._tasks[task_id]["end_time"] - self._tasks[task_id]["start_time"]
                ).total_seconds()
                if error:
                    self._tasks[task_id]["error"] = error

                self._task_stats["running"] -= 1
                if success:
                    self._task_stats["success"] += 1
                else:
                    self._task_stats["failed"] += 1

                if not success:
                    logger.error(f"任务失败: {task_id}", task_name=self._tasks[task_id]["task_name"], error=error)

                if len(self._tasks) > 1000:
                    oldest = sorted(self._tasks.items(), key=lambda x: x[1]["start_time"])[:100]
                    for tid, _ in oldest:
                        del self._tasks[tid]

    def get_stats(self) -> dict:
        """获取任务统计"""
        with self._lock:
            recent_failed = [
                t for t in self._tasks.values() if t["status"] == "failed"
            ][-10:]
            return {
                **self._task_stats,
                "recent_failed": recent_failed,
            }


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self._alerts: List[dict] = []
        self._alert_history: List[dict] = []
        self._suppressed: Dict[str, float] = {}
        self._handlers: List[Callable] = []

    def add_handler(self, handler: Callable):
        """添加告警处理函数"""
        self._handlers.append(handler)

    def trigger_alert(self, level: str, message: str, details: dict = None):
        """触发告警"""
        key = f"{level}:{message}"
        now = time.time()

        if key in self._suppressed and now - self._suppressed[key] < 300:
            return

        alert = {
            "id": f"alert_{int(now)}_{hash(key) % 1000}",
            "level": level,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
            "status": "active",
        }

        self._alerts.append(alert)
        self._alert_history.append(alert)
        self._suppressed[key] = now

        if len(self._alerts) > 50:
            self._alerts = self._alerts[-50:]
        if len(self._alert_history) > 500:
            self._alert_history = self._alert_history[-500:]

        logger.log(level, f"[ALERT] {message}", **(details or {}))

        for handler in self._handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(alert))
                else:
                    handler(alert)
            except Exception:
                logger.exception(f"告警处理器执行失败: {handler.__name__}")

    def resolve_alert(self, alert_id: str):
        """解决告警"""
        for alert in self._alerts:
            if alert["id"] == alert_id:
                alert["status"] = "resolved"
                alert["resolved_at"] = datetime.now().isoformat()
                break

    def get_alerts(self, status: str = "active") -> List[dict]:
        """获取告警列表"""
        if status == "all":
            return self._alert_history[-20:]
        return [a for a in self._alerts if a["status"] == status]

    def check_health(self, db_monitor: DatabaseMonitor, task_monitor: TaskMonitor):
        """执行健康检查"""
        db_stats = db_monitor.get_stats()
        task_stats = task_monitor.get_stats()

        if db_stats["pool_status"] == "critical":
            self.trigger_alert(
                "error",
                "数据库连接池接近上限",
                {"active": db_stats["active_connections"], "max": db_stats["max_connections"]},
            )

        if db_stats["connection_errors"] > 5:
            self.trigger_alert(
                "error",
                "数据库连接错误过多",
                {"errors": db_stats["connection_errors"]},
            )

        fail_rate = task_stats["total"] / max(task_stats["failed"], 1) if task_stats["total"] > 0 else 0
        if task_stats["failed"] > 10 or fail_rate > 0.3:
            self.trigger_alert(
                "warning",
                "任务失败率过高",
                {"failed": task_stats["failed"], "total": task_stats["total"], "rate": round(fail_rate, 2)},
            )


db_monitor = DatabaseMonitor()
task_monitor = TaskMonitor()
alert_manager = AlertManager()


def monitor_task(task_id: str, task_name: str):
    """任务监控装饰器"""
    def decorator(func):
        import functools
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            task_monitor.start_task(task_id, task_name)
            try:
                result = await func(*args, **kwargs)
                task_monitor.complete_task(task_id, success=True)
                return result
            except Exception as e:
                task_monitor.complete_task(task_id, success=False, error=str(e))
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            task_monitor.start_task(task_id, task_name)
            try:
                result = func(*args, **kwargs)
                task_monitor.complete_task(task_id, success=True)
                return result
            except Exception as e:
                task_monitor.complete_task(task_id, success=False, error=str(e))
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def get_system_status() -> dict:
    """获取系统状态摘要"""
    db_stats = db_monitor.get_stats()
    task_stats = task_monitor.get_stats()
    alerts = alert_manager.get_alerts("active")

    return {
        "timestamp": datetime.now().isoformat(),
        "database": db_stats,
        "tasks": task_stats,
        "alerts": {
            "count": len(alerts),
            "list": alerts,
        },
        "metrics": metrics.export(),
    }