"""Student profile routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..agents.profiler import ProfilerAgent
from ..db.repositories import ProfileRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/profile", tags=["profile"])
_profiler = ProfilerAgent()


class ProfileUpdateRequest(BaseModel):
    profile: dict


@router.get("/{user_id}")
def get_profile(user_id: str):
    try:
        return {"user_id": user_id, "profile": _profiler.get_profile(user_id)}
    except Exception as exc:
        logger.error("get profile failed user=%s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="profile read failed") from exc


@router.post("/{user_id}")
def update_profile(user_id: str, body: ProfileUpdateRequest):
    try:
        ProfileRepository.upsert(user_id, body.profile)
        return {"user_id": user_id, "status": "ok"}
    except Exception as exc:
        logger.error("update profile failed user=%s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="profile update failed") from exc
