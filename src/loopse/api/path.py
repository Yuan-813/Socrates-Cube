from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from src.loopse.agent.path_planner import path_planner
from src.loopse.db.repositories import ProfileRepository

router = APIRouter(prefix="/api/v1/path", tags=["路径"])


class PlanRequest(BaseModel):
    user_id: str
    target_topic: str = "TCP/IP协议"
    session_id: Optional[str] = None


@router.post("/plan")
async def plan_path(req: PlanRequest):
    profile = ProfileRepository.get(req.user_id) or {}
    result = path_planner.plan(
        user_id=req.user_id,
        profile=profile,
        target_topic=req.target_topic,
    )
    return result


@router.get("/{user_id}")
async def get_path(user_id: str):
    profile = ProfileRepository.get(user_id) or {}
    result = path_planner.plan(user_id=user_id, profile=profile)
    return result


@router.post("/{user_id}/progress")
async def update_progress(user_id: str, node_id: str, status: str):
    return {"success": True, "node_id": node_id, "status": status}
