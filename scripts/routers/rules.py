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


@router.post("/rules/scrape")
async def trigger_browser_scrape(platform: str | None = None):
    """手动触发浏览器采集（调试/手动刷新用）。

    不传 platform 时采集全部 13 个平台。
    """
    try:
        from monitors.browser import get_browser_pool, PlatformBrowser

        pool = await get_browser_pool()
        pb = PlatformBrowser(pool)

        if platform:
            result = await pb.scrape_platform(platform)
            return {
                "platform": platform,
                "success": result.success,
                "item_count": len(result.hot_items),
                "title_count": len(result.raw_titles),
                "topic_count": len(result.topics),
                "topics": result.topics[:10],
                "error": result.error,
            }

        results = await pb.scrape_all()
        return {
            "platforms": {
                p: {
                    "success": r.success,
                    "title_count": len(r.raw_titles),
                    "topic_count": len(r.topics),
                    "error": r.error,
                }
                for p, r in results.items()
            },
            "total_success": sum(1 for r in results.values() if r.success),
            "total_titles": sum(len(r.raw_titles) for r in results.values()),
        }
    except ImportError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"error": "浏览器采集不可用", "detail": str(e)},
        )


@router.get("/scraper/health")
async def scraper_health():
    """获取采集器健康状态（含浏览器池状态）"""
    return scheduler.scraper.get_health_metrics()


@router.get("/source-health")
async def source_health():
    """获取各平台数据源健康状态 — 用于前端展示数据可信度。

    返回每平台的数据来源（browser/api/fallback/seed/missing）
    和新鲜度（更新是否在12小时内）。
    """
    return scheduler.scraper.get_source_health()
