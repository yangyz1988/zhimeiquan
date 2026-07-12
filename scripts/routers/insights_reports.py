"""平台爆款规则分析报告 API

GET /api/insights/reports — 获取所有平台报告摘要（供 reports 页面使用）
GET /api/insights/reports/{platform} — 获取单平台完整报告
POST /api/insights/reports/refresh — 手动触发规则刷新 + 重新生成报告
"""

from fastapi import APIRouter

from services.report import ReportGenerator
from services.hotspot import HotspotService

router = APIRouter()
report_gen = ReportGenerator()
hotspot_svc = HotspotService()


@router.get("/reports")
async def get_all_reports():
    """获取所有平台的报告摘要（前端 reports 页面使用）"""
    reports = report_gen.generate_all_reports()
    return {"reports": reports, "total": len(reports)}


@router.get("/reports/{platform}")
async def get_platform_report(platform: str):
    """获取单平台完整报告"""
    report = report_gen.generate_platform_report(platform)
    if "error" in report:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=report["error"])
    return report


@router.post("/reports/refresh")
async def refresh_reports():
    """手动触发规则刷新 + 重新生成报告"""
    try:
        from monitors.scheduler import RuleScheduler
        scheduler = RuleScheduler(data_dir="../data/rules")
        result = await scheduler.update_all_rules()

        # 用新数据刷新 trending_topics
        for platform in result:
            titles = [h.get("title", "") for h in result[platform].get("hot_list", []) if h.get("title")]
            if titles:
                hotspot_svc.refresh_trending_topics(platform, titles, save=True)

        reports = report_gen.generate_all_reports()
        return {
            "status": "ok",
            "platforms_updated": list(result.keys()),
            "reports_generated": len(reports),
        }
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"error": str(e)})
