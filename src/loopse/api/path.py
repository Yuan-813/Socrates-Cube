"""Learning path routes."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..agents.path_planner import PathPlannerAgent
from ..agents.profiler import ProfilerAgent
from ..db.repositories import LearningPathRepository, ProfileRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/path", tags=["path"])
_planner = PathPlannerAgent()
_profiler = ProfilerAgent()


class PlanRequest(BaseModel):
    target_node_ids: Optional[list[str]] = None
    max_nodes: int = Field(default=10, ge=1, le=20)


class ProgressUpdateRequest(BaseModel):
    node_id: str
    status: str = Field(..., pattern="^(completed|in_progress|pending)$")
    mastery: Optional[float] = Field(default=None, ge=0.0, le=1.0)


@router.get("/{user_id}")
def get_user_path(user_id: str):
    try:
        path = _planner.plan(user_id, _profiler.get_profile(user_id))
        LearningPathRepository.save(path)
        return path
    except Exception as exc:
        logger.error("path planning failed user=%s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="path planning failed") from exc


@router.post("/plan")
def plan_path(req: PlanRequest, user_id: str = "student-001"):
    try:
        path = _planner.plan(user_id, _profiler.get_profile(user_id), req.target_node_ids, req.max_nodes)
        LearningPathRepository.save(path)
        return path
    except Exception as exc:
        logger.error("path planning failed: %s", exc)
        raise HTTPException(status_code=500, detail="path planning failed") from exc


@router.post("/{user_id}/progress")
def update_node_progress(user_id: str, req: ProgressUpdateRequest):
    try:
        profile = _profiler.get_profile(user_id)
        mastery_map = profile.get("mastery_map", {})
        if req.mastery is not None:
            mastery_map[req.node_id] = req.mastery
            profile["mastery_map"] = mastery_map
            profile["weak_points"] = [nid for nid, m in mastery_map.items() if m < 0.5]
            profile["strong_points"] = [nid for nid, m in mastery_map.items() if m >= 0.8]
            ProfileRepository.upsert(user_id, profile)
        return {"user_id": user_id, "node_id": req.node_id, "status": "updated"}
    except Exception as exc:
        logger.error("progress update failed user=%s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="progress update failed") from exc
