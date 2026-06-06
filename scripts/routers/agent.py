"""自主 Agent API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.agent import autonomous_agent

router = APIRouter()


class AutoTaskRequest(BaseModel):
    project_id: str
    platform: str
    topic: str
    frequency: str = "daily"
    time_of_day: str = "10:00"


@router.post("/create")
async def create_auto_task(req: AutoTaskRequest):
    """创建自动发布任务"""
    return autonomous_agent.create_auto_publish_task(
        req.project_id,
        req.platform,
        req.topic,
        req.frequency,
        req.time_of_day,
    )


@router.get("/tasks")
async def get_tasks():
    """获取所有自动任务"""
    return autonomous_agent.get_tasks()


@router.get("/activity")
async def get_activity(limit: int = 100):
    """获取活动日志"""
    return {"log": autonomous_agent.get_activity_log(limit)}
