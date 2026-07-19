"""Student profile routes.

响应格式：已迁移至 ApiResponse 统一包装（success/code/message/data）。
"""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..agent.profiler import ProfilerAgent, PROFILE_DIMENSIONS
from ..db.repositories import ProfileRepository, ResourceRepository
from ..schema.response import ok

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/profile", tags=["profile"])
_profiler = ProfilerAgent()


class ProfileUpdateRequest(BaseModel):
    profile: dict


@router.get("/{user_id}")
def get_profile(user_id: str):
    try:
        return ok(
            data={"user_id": user_id, "profile": _profiler.get_profile(user_id)},
            message="获取成功",
        )
    except Exception as exc:
        logger.error("get profile failed user=%s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="profile read failed") from exc


@router.post("/{user_id}")
def update_profile(user_id: str, body: ProfileUpdateRequest):
    try:
        ProfileRepository.upsert(user_id, body.profile)
        return ok(data={"user_id": user_id}, message="更新成功")
    except Exception as exc:
        logger.error("update profile failed user=%s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="profile update failed") from exc


@router.get("/{user_id}/report")
def get_profile_report(user_id: str):
    """导出用户学习成长报告，包含 8 维能力得分、薄弱知识点、已学资源统计、推荐考证路径。"""
    try:
        profile = _profiler.get_profile(user_id)

        # 8 维得分
        dim_labels = {
            "conceptual_understanding": "概念理解",
            "protocol_analysis":        "协议分析",
            "calculation_ability":      "计算能力",
            "error_diagnosis":          "错误诊断",
            "system_design":            "系统设计",
            "knowledge_connection":     "知识迁移",
            "expression_clarity":       "表达清晰",
            "self_correction":          "自我纠错",
        }
        dimensions = [
            {"key": k, "label": dim_labels[k], "score": round(profile.get(k, 0.5) * 100)}
            for k in PROFILE_DIMENSIONS
        ]
        overall = round(sum(d["score"] for d in dimensions) / len(dimensions))

        # 资源统计
        try:
            resources = ResourceRepository.list_recent(limit=200)
            resource_count = len(resources)
        except Exception:
            resource_count = 0

        # 推荐考证路径
        if overall >= 70:
            recommended_cert = "HCIA-Datacom 或 CCNA（基础春实，可充分指导）"
        elif overall >= 50:
            recommended_cert = "建议先完善薄弱知识点，再备考 HCIA-Datacom"
        else:
            recommended_cert = "继续学习基础网络知识，建议完成 Socrates Cube 课程后再备考"

        return {
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "overall_score": overall,
            "dimensions": dimensions,
            "weak_points": profile.get("weak_points", []),
            "strong_points": profile.get("strong_points", []),
            "turn_count": profile.get("turn_count", 0),
            "resource_count": resource_count,
            "recommended_cert": recommended_cert,
        }
    except Exception as exc:
        logger.error("report generation failed user=%s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="report generation failed") from exc
