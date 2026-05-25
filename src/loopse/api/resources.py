"""
/api/v1/resources 路由：学习资源生成与查询
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...agents.resource_generator import ResourceGeneratorAgent
from ...agents.retriever import RetrieverAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/resources", tags=["resources"])

_resource_gen = ResourceGeneratorAgent()
_retriever = RetrieverAgent()


class GenerateRequest(BaseModel):
    knowledge_point: str = Field(..., min_length=1, max_length=100)
    resource_type: str = Field(default="doc", pattern="^(doc|exercise|code)$")
    difficulty: int = Field(default=3, ge=1, le=5)
    session_id: str | None = None


@router.post("/generate")
async def generate_resource(req: GenerateRequest):
    """生成指定知识点的学习资源"""
    try:
        # 先检索相关文档作为上下文
        retrieval = _retriever.search_knowledge(req.knowledge_point, top_k=3)
        resource = _resource_gen.generate(
            resource_type=req.resource_type,
            knowledge_point=req.knowledge_point,
            context_docs=retrieval,
            difficulty=req.difficulty,
        )
        return resource
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("资源生成失败: %s", e)
        raise HTTPException(status_code=500, detail="资源生成失败")
