"""
/api/v1/path 路由：学习路径规划与进度追踪
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from ...agents.path_planner import PathPlannerAgent
from ...agents.profiler import ProfilerAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/path", tags=["path"])

_planner = PathPlannerAgent()
_profiler = ProfilerAgent()


@router.get("/{user_id}")
def get_user_path(user_id: str):
    """获取用户的推荐学习路径（基于当前画像自动规划）"""
    try:
        profile = _profiler.get_profile(user_id)
        path = _planner.plan(user_id, profile)
        return path
    except Exception as e:
        logger.error("路径规划失败 user=%s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="路径规划失败")


class PlanRequest(BaseModel):
    target_node_ids: Optional[List[str]] = None
    max_nodes: int = Field(default=10, ge=1, le=20)


@router.post("/plan")
def plan_path(req: PlanRequest, user_id: str = "student-001"):
    """指定目标知识点，重新规划学习路径"""
    try:
        profile = _profiler.get_profile(user_id)
        path = _planner.plan(user_id, profile, req.target_node_ids, req.max_nodes)
        return path
    except Exception as e:
        logger.error("路径规划失败: %s", e)
        raise HTTPException(status_code=500, detail="路径规划失败")


class ProgressUpdateRequest(BaseModel):
    node_id: str
    status: str = Field(..., pattern="^(completed|in_progress|pending)$")
    mastery: Optional[float] = Field(default=None, ge=0.0, le=1.0)


@router.post("/{user_id}/progress")
def update_node_progress(user_id: str, req: ProgressUpdateRequest):
    """更新用户某知识点的学习进度"""
    from ...db.repositories import ProfileRepository
    import json

    try:
        profile = _profiler.get_profile(user_id)
        mastery_map = profile.get("mastery_map", {})
        if req.mastery is not None:
            mastery_map[req.node_id] = req.mastery
            profile["mastery_map"] = mastery_map
            # 更新弱点列表
            profile["weak_points"] = [nid for nid, m in mastery_map.items() if m < 0.5]
            profile["strong_points"] = [nid for nid, m in mastery_map.items() if m >= 0.8]
            ProfileRepository.upsert(user_id, json.dumps(profile, ensure_ascii=False))
        return {"user_id": user_id, "node_id": req.node_id, "status": "updated"}
    except Exception as e:
        logger.error("进度更新失败: %s", e)
        raise HTTPException(status_code=500, detail="进度更新失败")
