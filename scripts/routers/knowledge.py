"""知识图谱 API 路由 — 搜索与索引

端点:
- GET  /api/v1/knowledge/search  搜索知识图谱
- POST /api/v1/knowledge/index   索引新知识条目
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.knowledge_graph import KnowledgeGraph

router = APIRouter()
kg = KnowledgeGraph(cache_enabled=True)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class IndexRequest(BaseModel):
    source: str = Field(
        ...,
        description="知识来源类型: methodology | template | prompt",
        pattern=r"^(methodology|template|prompt)$",
    )
    title: str = Field(..., min_length=1, max_length=256)
    content: str = Field(..., min_length=1, description="Markdown 格式的知识内容")
    tags: list[str] = Field(default_factory=list, description="分类标签")
    platform: str | None = Field(default=None, description="关联平台 (template 类型时使用)")


class SearchParams(BaseModel):
    query: str = Field(..., min_length=1, max_length=512, description="搜索关键词")
    category: str | None = Field(
        default=None,
        description="过滤类别: methodology | template | prompt | all",
        pattern=r"^(methodology|template|prompt|all)$",
    )
    platform: str | None = Field(default=None, description="按平台过滤")
    max_results: int = Field(default=10, ge=1, le=50)


# ---------------------------------------------------------------------------
# GET /api/v1/knowledge/search
# ---------------------------------------------------------------------------

@router.get("/search", summary="搜索知识图谱")
async def search_knowledge(
    query: str = Query(..., min_length=1, max_length=512, description="搜索关键词"),
    category: str | None = Query(
        default=None,
        description="过滤类别: methodology | template | prompt | all",
        pattern=r"^(methodology|template|prompt|all)$",
    ),
    platform: str | None = Query(default=None, description="按平台过滤 (template 类有效)"),
    max_results: int = Query(default=10, ge=1, le=50, description="最大返回数"),
):
    """在知识图谱中搜索与查询相关的内容。

    搜索范围覆盖：
    - 方法论文件（content/methodology/）
    - 平台模板（content/templates/）
    - 提示词库（content/prompts/）

    返回按相关度降序排列的结果列表，每条结果包含类型、评分、摘要。
    """
    results = kg.search(
        query=query,
        category=category,
        platform=platform,
        max_results=max_results,
    )

    return {
        "query": query,
        "category": category,
        "platform": platform,
        "total": len(results),
        "results": [
            {
                "type": r["type"],
                "score": round(r["score"], 2),
                "id": r.get("id"),
                "title": r.get("title"),
                "description": r.get("description", ""),
                "tags": r.get("tags", []),
                "source": r.get("source", ""),
            }
            for r in results
        ],
    }


# ---------------------------------------------------------------------------
# POST /api/v1/knowledge/index
# ---------------------------------------------------------------------------

@router.post("/index", summary="索引新知识条目")
async def index_knowledge(req: IndexRequest):
    """将新知识条目写入 content 目录并刷新知识图谱缓存。

    写入路径：
    - methodology → content/methodology/{slug}.md
    - template     → content/templates/{slug}-template.md
    - prompt       → content/prompts/{slug}.md

    索引完成后自动触发缓存刷新。
    """
    import re
    from pathlib import Path

    # 生成安全文件名
    slug = re.sub(r"[^\w\-]", "-", req.title.lower())[:64].strip("-") or "untitled"

    base = Path(__file__).resolve().parent.parent.parent  # PROJECT_ROOT
    dir_map = {
        "methodology": base / "content" / "methodology",
        "template": base / "content" / "templates",
        "prompt": base / "content" / "prompts",
    }
    file_pattern = {
        "methodology": f"{slug}.md",
        "template": f"{slug}-template.md",
        "prompt": f"{slug}.md",
    }

    target_dir = dir_map[req.source]
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / file_pattern[req.source]

    if target_file.exists():
        raise HTTPException(
            status_code=409,
            detail={
                "code": "already_exists",
                "message": f"知识条目已存在: {target_file.relative_to(base)}",
                "path": str(target_file.relative_to(base)),
            },
        )

    # 构建 Markdown 文件内容
    lines = [f"# {req.title}", ""]
    if req.platform:
        lines.append(f"> 平台: {req.platform}")
    if req.tags:
        lines.append(f"> 标签: {', '.join(req.tags)}")
    lines.extend(["", req.content])

    target_file.write_text("\n".join(lines), encoding="utf-8")

    # 强制刷新知识图谱缓存
    kg.refresh(force=True)

    return {
        "status": "indexed",
        "source": req.source,
        "title": req.title,
        "path": str(target_file.relative_to(base)),
        "tags": req.tags,
        "cache_refreshed": True,
    }


# ---------------------------------------------------------------------------
# 辅助端点
# ---------------------------------------------------------------------------

@router.get("/stats", summary="获取知识图谱统计信息")
async def get_knowledge_stats():
    """返回知识图谱的统计信息：条目数、分类、缓存状态。"""
    return kg.get_knowledge_stats()


@router.get("/categories", summary="获取所有方法论分类")
async def get_categories():
    """返回知识图谱中所有方法论分类标签。"""
    return {"categories": kg.get_all_categories()}


@router.get("/context", summary="获取主题相关上下文")
async def get_context(
    topic: str = Query(..., min_length=1, description="内容主题"),
    platform: str | None = Query(default=None, description="目标平台"),
    persona: str | None = Query(default=None, description="创作人设"),
    max_sources: int = Query(default=3, ge=1, le=10),
):
    """获取与主题相关的知识上下文文本，适合嵌入 Prompt。

    自动聚合方法论、平台模板、人设、提示词四类知识。
    """
    context_text = kg.get_relevant_context(
        topic=topic,
        platform=platform,
        persona=persona,
        max_sources=max_sources,
    )
    return {
        "topic": topic,
        "platform": platform,
        "persona": persona,
        "context": context_text,
    }


@router.get("/platform/{platform}", summary="获取平台知识")
async def get_platform_knowledge(platform: str):
    """获取指定平台的全部知识（模板 + 相关方法论）。"""
    return kg.get_platform_knowledge(platform)
