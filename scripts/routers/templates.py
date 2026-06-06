"""模板 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.templates import TemplateService

router = APIRouter()
service = TemplateService()


class TemplateRequest(BaseModel):
    id: str
    name: str
    category: str
    platform: str
    structure: list[dict]


class ApplyRequest(BaseModel):
    template_id: str
    variables: dict[str, str]


@router.get("/list")
async def list_templates(category: str | None = None, platform: str | None = None):
    """列出模板"""
    return service.list_templates(category=category, platform=platform)


@router.get("/{template_id}")
async def get_template(template_id: str):
    """获取模板"""
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.post("/")
async def save_template(req: TemplateRequest):
    """保存模板"""
    return service.save_template(req.model_dump())


@router.post("/apply")
async def apply_template(req: ApplyRequest):
    """应用模板"""
    result = service.apply_template(req.template_id, req.variables)
    if not result:
        raise HTTPException(status_code=404, detail="模板不存在")
    return result
