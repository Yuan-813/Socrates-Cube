"""Learning resource routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..agent.resource_generator import ResourceGeneratorAgent
from ..agent.retriever import RetrieverAgent
from ..db.repositories import ResourceRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/resources", tags=["resources"])
_resource_gen = ResourceGeneratorAgent()
_retriever = RetrieverAgent()


class GenerateRequest(BaseModel):
    knowledge_point: str = Field(..., min_length=1, max_length=100)
    resource_type: str = Field(default="doc", pattern="^(doc|exercise|code|mindmap|script|infographic|all)$")
    difficulty: int = Field(default=3, ge=1, le=5)
    session_id: str | None = None


@router.get("/")
def list_resources(limit: int = 20):
    return {"items": ResourceRepository.list_recent(limit=limit)}


@router.post("/generate")
async def generate_resource(req: GenerateRequest):
    try:
        retrieval = _retriever.search_knowledge(req.knowledge_point, top_k=3)
        if req.resource_type == "all":
            return _resource_gen.generate_all(
                knowledge_point=req.knowledge_point,
                context_docs=retrieval,
                difficulty=req.difficulty,
            )
        return _resource_gen.generate(
            resource_type=req.resource_type,
            knowledge_point=req.knowledge_point,
            context_docs=retrieval,
            difficulty=req.difficulty,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("resource generation failed: %s", exc)
        raise HTTPException(status_code=500, detail="resource generation failed") from exc


@router.post("/generate-all")
async def generate_all_resources(req: GenerateRequest):
    """一次性生成五类资源：知识文档、练习题、代码示例、思维导图、视频脚本"""
    try:
        retrieval = _retriever.search_knowledge(req.knowledge_point, top_k=3)
        return _resource_gen.generate_all(
            knowledge_point=req.knowledge_point,
            context_docs=retrieval,
            difficulty=req.difficulty,
        )
    except Exception as exc:
        logger.error("all resources generation failed: %s", exc)
        raise HTTPException(status_code=500, detail="resources generation failed") from exc
