"""A/B 测试管理 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.data_loop import ABTester

router = APIRouter()
tester = ABTester(data_dir="../data/ab_tests")


class CreateTestRequest(BaseModel):
    test_id: str
    project_id: str
    variants: list[dict]


class UpdateVariantRequest(BaseModel):
    variant_id: str
    metrics: dict


@router.post("/create")
async def create_ab_test(req: CreateTestRequest):
    """创建 A/B 测试"""
    test = tester.create_test(req.test_id, req.project_id, req.variants)
    return test


@router.post("/{test_id}/update")
async def update_variant(test_id: str, req: UpdateVariantRequest):
    """更新变体数据"""
    result = tester.update_variant_metrics(test_id, req.variant_id, req.metrics)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/{test_id}/result")
async def get_test_result(test_id: str):
    """获取测试结果"""
    result = tester.get_winner(test_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
