from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from src.loopse.agent.resource_generator import resource_generator
from src.loopse.agent.retriever import retriever_agent

router = APIRouter(prefix="/api/v1/resources", tags=["资源"])


class GenerateRequest(BaseModel):
    knowledge_point: str
    resource_types: List[str] = ["doc", "exercise", "code"]
    cognitive_style: str = "textual"
    error_type: str = ""
    session_id: Optional[str] = None


@router.post("/generate")
async def generate_resources(req: GenerateRequest):
    search_results = retriever_agent.search_knowledge(req.knowledge_point, n_results=3)
    reference_content = "\n\n".join([r["content"] for r in search_results])
    source_chapter = search_results[0]["metadata"].get("chapter", "") if search_results else ""

    resources = resource_generator.generate(
        knowledge_point=req.knowledge_point,
        resource_types=req.resource_types,
        cognitive_style=req.cognitive_style,
        error_type=req.error_type,
        reference_content=reference_content,
        source_chapter=source_chapter,
    )
    return {"resources": resources, "count": len(resources)}


@router.get("")
async def list_resources(session_id: Optional[str] = None):
    return {"resources": [], "message": "Phase 4: 将从DB查询"}
