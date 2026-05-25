"""
/api/v1/profile 路由：学生画像读写
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...agents.profiler import ProfilerAgent, _DEFAULT_PROFILE

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/profile", tags=["profile"])
_profiler = ProfilerAgent()


@router.get("/{user_id}")
def get_profile(user_id: str):
    """获取指定用户的学习画像"""
    try:
        profile = _profiler.get_profile(user_id)
        return {"user_id": user_id, "profile": profile}
    except Exception as e:
        logger.error("获取画像失败 user=%s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="画像读取失败")


class ProfileUpdateRequest(BaseModel):
    profile: dict


@router.post("/{user_id}")
def update_profile(user_id: str, body: ProfileUpdateRequest):
    """直接覆盖写入学生画像（用于前端手动调整）"""
    from ...db.repositories import ProfileRepository
    try:
        ProfileRepository.upsert(user_id, json.dumps(body.profile, ensure_ascii=False))
        return {"user_id": user_id, "status": "ok"}
    except Exception as e:
        logger.error("更新画像失败 user=%s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="画像更新失败")
