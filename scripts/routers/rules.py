import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from monitors.scheduler import RuleScheduler

router = APIRouter()
scheduler = RuleScheduler(data_dir="../data/rules")


class RulesResponse(BaseModel):
    updated_at: str | None
    platforms: list[str]
    rules: dict


class PlatformRuleResponse(BaseModel):
    platform: str
    rules: dict


@router.get("/rules", response_model=RulesResponse)
async def get_all_rules():
    """获取所有平台爆款规则"""
    data = scheduler.load_rules()
    if not data:
        return RulesResponse(updated_at=None, platforms=[], rules={})
    return RulesResponse(
        updated_at=data.get("updated_at"),
        platforms=data.get("platforms", []),
        rules=data.get("rules", {}),
    )


@router.get("/rules/{platform}", response_model=PlatformRuleResponse)
async def get_platform_rules(platform: str):
    """获取单平台爆款规则"""
    rules = scheduler.load_rules(platform)
    if not rules:
        raise HTTPException(status_code=404, detail=f"{platform} 规则不存在")
    return PlatformRuleResponse(platform=platform, rules=rules)


@router.post("/rules/refresh")
async def refresh_rules():
    """手动刷新所有平台规则"""
    try:
        result = await scheduler.update_all_rules()
        return {"status": "ok", "platforms": list(result.keys())}
    except Exception as e:
        raise HTTPException(status_code=500, detail="规则刷新失败，请稍后重试")


@router.get("/rules/status")
async def rules_status():
    """检查规则状态"""
    status = scheduler.get_rules_age()
    return status
