from fastapi import APIRouter
from src.loopse.db.repositories import ProfileRepository

router = APIRouter(prefix="/api/v1/profile", tags=["画像"])


@router.get("/{user_id}")
async def get_profile(user_id: str):
    profile = await ProfileRepository.get(user_id)
    if not profile:
        return {"user_id": user_id, "profile": None, "message": "尚未建立画像"}
    return {"user_id": user_id, "profile": profile}


@router.post("/{user_id}")
async def update_profile(user_id: str, profile: dict):
    await ProfileRepository.upsert(user_id, profile)
    return {"success": True}
