"""内容调度 API"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.scheduler_service import content_scheduler

router = APIRouter()


class ScheduleRequest(BaseModel):
    project_id: str
    content_id: str
    platform: str
    title: str
    content: str
    scheduled_at: datetime


class RecurringRequest(BaseModel):
    project_id: str
    platform: str
    title_template: str
    cron: str


@router.post("/schedule")
async def schedule_post(req: ScheduleRequest):
    """调度一次性发布"""
    return content_scheduler.schedule_post(
        req.project_id,
        req.content_id,
        req.platform,
        req.title,
        req.content,
        req.scheduled_at,
    )


@router.post("/recurring")
async def schedule_recurring(req: RecurringRequest):
    """调度周期性发布"""
    try:
        return content_scheduler.schedule_recurring(
            req.project_id,
            req.platform,
            req.title_template,
            req.cron,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/calendar/{year}/{month}")
async def get_calendar(year: int, month: int):
    """获取日历视图"""
    return content_scheduler.get_calendar(year, month)


@router.get("/queue")
async def get_queue():
    """获取调度队列"""
    return content_scheduler.get_queue()


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """取消调度任务"""
    success = content_scheduler.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"cancelled": True, "job_id": job_id}
