"""自动化工作流引擎 - 条件-动作系统

支持多种触发器和动作类型的自动化工作流管理。
工作流以 JSON 格式存储在 data/workflows/ 目录。
"""

import asyncio
import json
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from services.logging import logger


# 工作流存储目录
WORKFLOWS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "workflows"


def _ensure_workflows_dir():
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)


# ====== 触发器基类 ======

class Trigger(ABC):
    """触发器基类"""

    @abstractmethod
    def evaluate(self, context: dict | None = None) -> bool:
        """评估触发条件是否满足"""
        ...

    @abstractmethod
    def to_dict(self) -> dict:
        """序列化为字典"""
        ...

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> "Trigger":
        """反序列化"""
        ...

    def get_type(self) -> str:
        return self.__class__.__name__.replace("Trigger", "").lower()


class TimeTrigger(Trigger):
    """时间触发器 - 基于 cron 表达式

    cron 格式: minute hour dayOfMonth month dayOfWeek
    示例: "0 9 * * *" = 每天 9:00
    """

    def __init__(self, cron_expression: str, timezone: str = "Asia/Shanghai"):
        self.cron_expression = cron_expression
        self.timezone = timezone
        self._last_triggered: str | None = None

    def evaluate(self, context: dict | None = None) -> bool:
        now = datetime.now()
        parts = self.cron_expression.strip().split()

        if len(parts) != 5:
            logger.warning(f"无效的 cron 表达式: {self.cron_expression}")
            return False

        minute_pattern, hour_pattern, day_pattern, month_pattern, week_pattern = parts

        # 检查分钟
        if minute_pattern != "*":
            try:
                if int(minute_pattern) != now.minute:
                    return False
            except ValueError:
                pass

        # 检查小时
        if hour_pattern != "*":
            try:
                if int(hour_pattern) != now.hour:
                    return False
            except ValueError:
                pass

        # 检查星期
        if week_pattern != "*":
            try:
                weekday = now.weekday() + 1  # 1=Monday ... 7=Sunday
                if "-" in week_pattern:
                    start, end = week_pattern.split("-")
                    if not (int(start) <= weekday <= int(end)):
                        return False
                elif "," in week_pattern:
                    if weekday not in [int(w) for w in week_pattern.split(",")]:
                        return False
                elif int(week_pattern) != weekday:
                    return False
            except ValueError:
                pass

        # 检查日
        if day_pattern != "*":
            try:
                if int(day_pattern) != now.day:
                    return False
            except ValueError:
                pass

        # 检查月
        if month_pattern != "*":
            try:
                if int(month_pattern) != now.month:
                    return False
            except ValueError:
                pass

        # 防止同分钟内重复触发
        now_key = now.strftime("%Y-%m-%d %H:%M")
        if self._last_triggered == now_key:
            return False
        self._last_triggered = now_key
        return True

    def to_dict(self) -> dict:
        return {
            "type": "time",
            "cron_expression": self.cron_expression,
            "timezone": self.timezone,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TimeTrigger":
        return cls(
            cron_expression=data.get("cron_expression", "0 9 * * *"),
            timezone=data.get("timezone", "Asia/Shanghai"),
        )


class HotTopicTrigger(Trigger):
    """热搜触发器 - 当热榜出现匹配关键词时触发"""

    def __init__(self, keywords: list[str], platform: str = "抖音", min_rank: int = 50):
        self.keywords = [k.lower() for k in keywords]
        self.platform = platform
        self.min_rank = min_rank
        self._matched: list[str] = []

    def evaluate(self, context: dict | None = None) -> bool:
        if not context:
            return False

        hot_topics = context.get("hot_topics", [])
        if not hot_topics:
            return False

        matched = []
        for topic in hot_topics:
            topic_str = topic if isinstance(topic, str) else topic.get("title", "")
            topic_lower = topic_str.lower()
            if any(kw in topic_lower for kw in self.keywords):
                matched.append(topic_str)

        if matched:
            self._matched = matched
            return True
        return False

    def get_matched_topics(self) -> list[str]:
        return self._matched

    def to_dict(self) -> dict:
        return {
            "type": "hot_topic",
            "keywords": self.keywords,
            "platform": self.platform,
            "min_rank": self.min_rank,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HotTopicTrigger":
        return cls(
            keywords=data.get("keywords", []),
            platform=data.get("platform", "抖音"),
            min_rank=data.get("min_rank", 50),
        )


class PerformanceTrigger(Trigger):
    """表现触发器 - 当内容指标低于阈值时触发"""

    def __init__(
        self,
        metric: str = "engagement_rate",
        threshold: float = 0.05,
        direction: str = "below",
        window_days: int = 7,
    ):
        self.metric = metric  # views, likes, engagement_rate, fire_score
        self.threshold = threshold
        self.direction = direction  # below / above
        self.window_days = window_days

    def evaluate(self, context: dict | None = None) -> bool:
        if not context:
            return False

        records = context.get("recent_records", [])
        if not records:
            return False

        # 计算最近 window_days 天的平均指标
        recent_values = []
        cutoff = datetime.now() - timedelta(days=self.window_days)

        for record in records:
            created = record.get("created_at") or record.get("published_at")
            if created:
                try:
                    dt = datetime.fromisoformat(created)
                    if dt < cutoff:
                        continue
                except (ValueError, TypeError):
                    pass

            if self.metric == "engagement_rate":
                metrics = record.get("metrics", {})
                views = metrics.get("views", 0)
                if views > 0:
                    eng = (
                        metrics.get("likes", 0)
                        + metrics.get("comments", 0)
                        + metrics.get("shares", 0)
                    ) / views
                    recent_values.append(eng)
            elif self.metric == "fire_score":
                score = record.get("fire_score")
                if score is not None:
                    recent_values.append(score)
            else:
                metrics = record.get("metrics", {})
                val = metrics.get(self.metric, 0)
                recent_values.append(val)

        if not recent_values:
            return False

        avg_value = sum(recent_values) / len(recent_values)

        if self.direction == "below":
            return avg_value < self.threshold
        else:
            return avg_value > self.threshold

    def to_dict(self) -> dict:
        return {
            "type": "performance",
            "metric": self.metric,
            "threshold": self.threshold,
            "direction": self.direction,
            "window_days": self.window_days,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PerformanceTrigger":
        return cls(
            metric=data.get("metric", "engagement_rate"),
            threshold=data.get("threshold", 0.05),
            direction=data.get("direction", "below"),
            window_days=data.get("window_days", 7),
        )


class ScheduleTrigger(Trigger):
    """计划触发器 - 在指定的具体时间执行"""

    def __init__(self, scheduled_time: str, repeat: bool = False):
        self.scheduled_time = scheduled_time  # ISO 格式 "2026-07-01T10:00:00"
        self.repeat = repeat
        self._fired = False

    def evaluate(self, context: dict | None = None) -> bool:
        if self._fired and not self.repeat:
            return False

        now = datetime.now()
        try:
            target = datetime.fromisoformat(self.scheduled_time)
            # 允许 1 分钟误差窗口
            if target <= now <= target + timedelta(minutes=1):
                self._fired = True
                return True
        except (ValueError, TypeError):
            pass
        return False

    def reset(self):
        self._fired = False

    def to_dict(self) -> dict:
        return {
            "type": "schedule",
            "scheduled_time": self.scheduled_time,
            "repeat": self.repeat,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleTrigger":
        return cls(
            scheduled_time=data.get("scheduled_time", ""),
            repeat=data.get("repeat", False),
        )


TriggerRegistry: dict[str, type[Trigger]] = {
    "time": TimeTrigger,
    "hot_topic": HotTopicTrigger,
    "performance": PerformanceTrigger,
    "schedule": ScheduleTrigger,
}


def trigger_from_dict(data: dict) -> Trigger:
    """根据字典反序列化触发器"""
    trigger_type = data.get("type", "")
    cls = TriggerRegistry.get(trigger_type)
    if cls is None:
        raise ValueError(f"未知触发器类型: {trigger_type}")
    return cls.from_dict(data)


# ====== 动作基类 ======

class Action(ABC):
    """动作基类"""

    @abstractmethod
    def execute(self, context: dict | None = None) -> dict:
        """执行动作"""
        ...

    @abstractmethod
    def to_dict(self) -> dict:
        ...

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> "Action":
        ...

    def get_type(self) -> str:
        return self.__class__.__name__.replace("Action", "").lower()


class GenerateAction(Action):
    """生成内容动作"""

    def __init__(self, topic: str, platform: str = "抖音", count: int = 1):
        self.topic = topic
        self.platform = platform
        self.count = count

    def execute(self, context: dict | None = None) -> dict:
        resolved_topic = self.topic
        if context and "{topic}" in resolved_topic:
            resolved_topic = resolved_topic.replace("{topic}", context.get("matched_topic", self.topic))

        logger.info(f"执行生成动作: {resolved_topic} ({self.platform}) x{self.count}")
        # 实际生成逻辑由外部服务接管
        return {
            "action": "generate",
            "topic": resolved_topic,
            "platform": self.platform,
            "count": self.count,
            "status": "queued",
            "executed_at": datetime.now().isoformat(),
        }

    def to_dict(self) -> dict:
        return {
            "type": "generate",
            "topic": self.topic,
            "platform": self.platform,
            "count": self.count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GenerateAction":
        return cls(
            topic=data.get("topic", ""),
            platform=data.get("platform", "抖音"),
            count=data.get("count", 1),
        )


class RewriteAction(Action):
    """改写内容动作"""

    def __init__(self, content_id: str, style: str = "optimize"):
        self.content_id = content_id
        self.style = style  # optimize / expand / shorten / adapt_platform

    def execute(self, context: dict | None = None) -> dict:
        logger.info(f"执行改写动作: {self.content_id} ({self.style})")
        return {
            "action": "rewrite",
            "content_id": self.content_id,
            "style": self.style,
            "status": "queued",
            "executed_at": datetime.now().isoformat(),
        }

    def to_dict(self) -> dict:
        return {
            "type": "rewrite",
            "content_id": self.content_id,
            "style": self.style,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RewriteAction":
        return cls(
            content_id=data.get("content_id", ""),
            style=data.get("style", "optimize"),
        )


class PublishAction(Action):
    """发布内容动作"""

    def __init__(self, platform: str, content_id: str | None = None):
        self.platform = platform
        self.content_id = content_id

    def execute(self, context: dict | None = None) -> dict:
        cid = self.content_id
        if not cid and context:
            cid = context.get("generated_content_id")

        logger.info(f"执行发布动作: {cid} -> {self.platform}")
        return {
            "action": "publish",
            "platform": self.platform,
            "content_id": cid,
            "status": "queued",
            "executed_at": datetime.now().isoformat(),
        }

    def to_dict(self) -> dict:
        return {
            "type": "publish",
            "platform": self.platform,
            "content_id": self.content_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PublishAction":
        return cls(
            platform=data.get("platform", "抖音"),
            content_id=data.get("content_id"),
        )


class NotifyAction(Action):
    """通知动作"""

    def __init__(self, message: str, channel: str = "log"):
        self.message = message
        self.channel = channel  # log / email / webhook

    def execute(self, context: dict | None = None) -> dict:
        resolved_msg = self.message
        if context:
            for key, value in context.items():
                placeholder = "{" + key + "}"
                if placeholder in resolved_msg:
                    resolved_msg = resolved_msg.replace(placeholder, str(value))

        logger.info(f"通知: {resolved_msg} (通过 {self.channel})")
        return {
            "action": "notify",
            "message": resolved_msg,
            "channel": self.channel,
            "status": "sent",
            "executed_at": datetime.now().isoformat(),
        }

    def to_dict(self) -> dict:
        return {
            "type": "notify",
            "message": self.message,
            "channel": self.channel,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NotifyAction":
        return cls(
            message=data.get("message", ""),
            channel=data.get("channel", "log"),
        )


class AnalyzeAction(Action):
    """分析动作"""

    def __init__(self, analysis_type: str, platform: str = "抖音", days: int = 7):
        self.analysis_type = analysis_type  # trends / performance / competition
        self.platform = platform
        self.days = days

    def execute(self, context: dict | None = None) -> dict:
        logger.info(f"执行分析动作: {self.analysis_type} ({self.platform}, {self.days}天)")
        return {
            "action": "analyze",
            "analysis_type": self.analysis_type,
            "platform": self.platform,
            "days": self.days,
            "status": "queued",
            "executed_at": datetime.now().isoformat(),
        }

    def to_dict(self) -> dict:
        return {
            "type": "analyze",
            "analysis_type": self.analysis_type,
            "platform": self.platform,
            "days": self.days,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AnalyzeAction":
        return cls(
            analysis_type=data.get("analysis_type", "trends"),
            platform=data.get("platform", "抖音"),
            days=data.get("days", 7),
        )


ActionRegistry: dict[str, type[Action]] = {
    "generate": GenerateAction,
    "rewrite": RewriteAction,
    "publish": PublishAction,
    "notify": NotifyAction,
    "analyze": AnalyzeAction,
}


def action_from_dict(data: dict) -> Action:
    """根据字典反序列化动作"""
    action_type = data.get("type", "")
    cls = ActionRegistry.get(action_type)
    if cls is None:
        raise ValueError(f"未知动作类型: {action_type}")
    return cls.from_dict(data)


# ====== 工作流引擎 ======

class AutomationEngine:
    """自动化工作流引擎"""

    def __init__(self, workflows_dir: str | Path = WORKFLOWS_DIR):
        self.workflows_dir = Path(workflows_dir)
        _ensure_workflows_dir()

    def _workflow_path(self, workflow_id: str) -> Path:
        return self.workflows_dir / f"{workflow_id}.json"

    def _load_workflow(self, workflow_id: str) -> dict | None:
        path = self._workflow_path(workflow_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载工作流失败 {workflow_id}: {e}")
            return None

    def _save_workflow(self, workflow_id: str, data: dict):
        path = self._workflow_path(workflow_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _delete_workflow_file(self, workflow_id: str) -> bool:
        path = self._workflow_path(workflow_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def _generate_id(self) -> str:
        return f"wf_{int(time.time() * 1000)}_{datetime.now().strftime('%Y%m%d')}"

    def create_workflow(
        self,
        user_id: str,
        name: str,
        trigger: Trigger,
        actions: list[Action],
    ) -> dict:
        """创建工作流

        Args:
            user_id: 用户 ID
            name: 工作流名称
            trigger: 触发器实例
            actions: 动作实例列表
        """
        workflow_id = self._generate_id()
        now = datetime.now().isoformat()

        workflow = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "name": name,
            "status": "active",
            "trigger": trigger.to_dict(),
            "actions": [a.to_dict() for a in actions],
            "stats": {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "last_execution": None,
            },
            "created_at": now,
            "updated_at": now,
        }

        self._save_workflow(workflow_id, workflow)
        logger.info(f"创建工作流: {name} ({workflow_id})")
        return workflow

    def list_workflows(self, user_id: str) -> list[dict]:
        """列出用户的所有工作流"""
        workflows = []
        for f in sorted(self.workflows_dir.glob("*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    wf = json.load(fh)
                if wf.get("user_id") == user_id:
                    workflows.append(wf)
            except Exception as e:
                logger.warning(f"加载工作流文件失败 {f.name}: {e}")
        return workflows

    def get_workflow(self, workflow_id: str) -> dict | None:
        """获取单个工作流"""
        return self._load_workflow(workflow_id)

    def update_workflow(self, workflow_id: str, config: dict) -> dict | None:
        """更新工作流配置

        Args:
            workflow_id: 工作流 ID
            config: 要更新的字段，如 {"name": "新名称", "status": "paused"}
        """
        workflow = self._load_workflow(workflow_id)
        if not workflow:
            return None

        # 允许更新的字段
        allowed_fields = {"name", "status", "trigger", "actions"}
        for key, value in config.items():
            if key in allowed_fields:
                workflow[key] = value

        # 如果是更新 trigger 或 actions，先序列化为 dict
        if "trigger" in config and isinstance(config["trigger"], Trigger):
            workflow["trigger"] = config["trigger"].to_dict()
        if "actions" in config:
            if config["actions"] and isinstance(config["actions"][0], Action):
                workflow["actions"] = [a.to_dict() for a in config["actions"]]

        workflow["updated_at"] = datetime.now().isoformat()
        self._save_workflow(workflow_id, workflow)
        logger.info(f"更新工作流: {workflow_id}")
        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        result = self._delete_workflow_file(workflow_id)
        if result:
            logger.info(f"删除工作流: {workflow_id}")
        return result

    def execute_workflow(
        self, workflow_id: str, context: dict | None = None
    ) -> dict:
        """立即执行工作流

        Args:
            workflow_id: 工作流 ID
            context: 执行上下文数据

        Returns:
            执行结果，包含每个动作的执行详情
        """
        workflow = self._load_workflow(workflow_id)
        if not workflow:
            return {"status": "error", "message": f"工作流不存在: {workflow_id}"}

        if workflow.get("status") != "active":
            return {"status": "skipped", "message": f"工作流状态为 {workflow.get('status')}，不执行"}

        action_results = []
        has_error = False

        for action_dict in workflow.get("actions", []):
            try:
                action = action_from_dict(action_dict)
                result = action.execute(context or {})
                action_results.append(result)
                if result.get("status") == "error":
                    has_error = True
            except Exception as e:
                logger.error(f"执行动作失败: {e}")
                action_results.append({
                    "action": action_dict.get("type", "unknown"),
                    "status": "error",
                    "error": str(e),
                })
                has_error = True

        # 更新统计
        workflow["stats"]["total_executions"] = workflow["stats"].get("total_executions", 0) + 1
        if has_error:
            workflow["stats"]["failed_executions"] = workflow["stats"].get("failed_executions", 0) + 1
        else:
            workflow["stats"]["successful_executions"] = workflow["stats"].get("successful_executions", 0) + 1
        workflow["stats"]["last_execution"] = datetime.now().isoformat()
        workflow["updated_at"] = datetime.now().isoformat()
        self._save_workflow(workflow_id, workflow)

        return {
            "workflow_id": workflow_id,
            "name": workflow.get("name"),
            "status": "completed" if not has_error else "completed_with_errors",
            "action_results": action_results,
            "executed_at": datetime.now().isoformat(),
        }

    def check_triggers(self, user_id: str, context: dict | None = None) -> list[dict]:
        """检查用户的所有活跃工作流，触发条件满足的立即执行

        Args:
            user_id: 用户 ID
            context: 评估上下文（如热搜数据、表现数据）

        Returns:
            被触发执行的工作流列表
        """
        workflows = self.list_workflows(user_id)
        triggered = []

        for wf in workflows:
            if wf.get("status") != "active":
                continue

            try:
                trigger = trigger_from_dict(wf["trigger"])
                if trigger.evaluate(context):
                    result = self.execute_workflow(wf["workflow_id"], context)
                    triggered.append({
                        "workflow_id": wf["workflow_id"],
                        "name": wf.get("name", ""),
                        "result": result,
                    })
            except Exception as e:
                logger.error(f"检查触发器失败 {wf.get('workflow_id')}: {e}")

        if triggered:
            logger.info(f"触发了 {len(triggered)} 个工作流")
        return triggered

    def get_workflow_stats(self, user_id: str) -> dict:
        """获取用户工作流统计"""
        workflows = self.list_workflows(user_id)
        total = len(workflows)
        active = sum(1 for w in workflows if w.get("status") == "active")
        paused = sum(1 for w in workflows if w.get("status") == "paused")
        total_executions = sum(
            w.get("stats", {}).get("total_executions", 0) for w in workflows
        )
        total_success = sum(
            w.get("stats", {}).get("successful_executions", 0) for w in workflows
        )
        total_failed = sum(
            w.get("stats", {}).get("failed_executions", 0) for w in workflows
        )

        return {
            "user_id": user_id,
            "total_workflows": total,
            "active_workflows": active,
            "paused_workflows": paused,
            "total_executions": total_executions,
            "successful_executions": total_success,
            "failed_executions": total_failed,
            "success_rate": round(
                total_success / max(total_executions, 1) * 100, 1
            ),
            "workflow_list": [
                {
                    "id": w["workflow_id"],
                    "name": w.get("name", ""),
                    "status": w.get("status", "unknown"),
                    "trigger_type": w.get("trigger", {}).get("type", ""),
                    "actions_count": len(w.get("actions", [])),
                    "last_execution": w.get("stats", {}).get("last_execution"),
                    "created_at": w.get("created_at"),
                }
                for w in workflows
            ],
        }


# 全局实例
automation_engine = AutomationEngine()
