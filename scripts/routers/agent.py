"""自主 Agent API"""

from datetime import datetime
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


class AgentStartRequest(BaseModel):
    keyword: str
    platform: str
    task_type: str = "cold_start"


@router.post("/start")
async def start_agent(req: AgentStartRequest):
    """启动 Agent 任务（冷启动/评论区/裂变/发布策略）"""
    task_id = f"agent_{req.platform}_{int(datetime.now().timestamp())}"
    result = autonomous_agent.create_auto_publish_task(
        project_id=f"ops_{task_id}",
        platform=req.platform,
        topic=req.keyword,
        frequency="once",
        time_of_day=datetime.now().strftime("%H:%M"),
    )
    return {
        "agentId": task_id,
        "taskId": result.get("task_id", task_id),
        "status": "running",
        "message": f"Agent 已启动: {req.task_type} / {req.platform} / {req.keyword}",
        "created_at": datetime.now().isoformat(),
    }


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
