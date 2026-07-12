"""竞品监控 API - 带认证保护"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from monitors.competitor import CompetitorMonitor

router = APIRouter()
monitor = CompetitorMonitor()


class AddCompetitorRequest(BaseModel):
    user_id: str
    platform: str
    account_id: str
    account_name: str


class RecordContentRequest(BaseModel):
    competitor_id: str
    content_data: dict


def _get_auth_user(request: Request) -> str:
    """获取认证用户ID，未认证则抛出401"""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="未授权访问")
    return user_id


@router.post("/add")
async def add_competitor(request: Request, req: AddCompetitorRequest):
    """添加竞品账号"""
    auth_user_id = _get_auth_user(request)
    # 强制使用认证用户ID，防止用户伪造
    result = monitor.add_competitor(auth_user_id, req.platform, req.account_id, req.account_name)
    if "error" in result:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=409, content=result)
    return result


@router.delete("/{competitor_id}")
async def remove_competitor(request: Request, competitor_id: str):
    """移除竞品账号"""
    _get_auth_user(request)  # 验证认证
    ok = monitor.remove_competitor(competitor_id)
    if not ok:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "竞品账号不存在"})
    return {"success": True}


@router.get("/list")
async def list_competitors(request: Request):
    """列出用户监控的所有竞品"""
    auth_user_id = _get_auth_user(request)
    return {"competitors": monitor.list_competitors(auth_user_id)}


@router.get("/analyze/{competitor_id}")
async def analyze_competitor(request: Request, competitor_id: str):
    """分析竞品内容策略"""
    _get_auth_user(request)  # 验证认证
    return monitor.analyze_competitor(competitor_id)


@router.get("/compare/{competitor_id}")
async def compare_with_competitor(request: Request, competitor_id: str):
    """对比用户与竞品的表现差异"""
    auth_user_id = _get_auth_user(request)
    return monitor.get_comparison(auth_user_id, competitor_id)


@router.post("/record")
async def record_content(request: Request, req: RecordContentRequest):
    """记录竞品发布的内容"""
    _get_auth_user(request)  # 验证认证
    result = monitor.record_content(req.competitor_id, req.content_data)
    if "error" in result:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=409, content=result)
    return result
