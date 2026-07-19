"""AI 人格系统 API。

提供人格列表查询与切换功能，人格配置存储在 config/agent_personas.json。
人格 ID 持久化到用户画像 profile_json 中的 persona_id 字段。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..agent.profiler import ProfilerAgent
from ..db.repositories import ProfileRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/persona", tags=["persona"])

_PERSONAS_PATH = Path("config/agent_personas.json")
_profiler = ProfilerAgent()


def _load_personas() -> dict:
    try:
        return json.loads(_PERSONAS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("[Persona] 加载人格配置失败: %s", exc)
        return {}


class PersonaSwitchRequest(BaseModel):
    user_id: str = "student-001"
    persona_id: str


@router.get("/list")
def list_personas():
    """获取所有可用的 AI 人格列表。"""
    personas = _load_personas()
    return {
        "personas": [
            {
                "id": pid,
                "name": pdata.get("name", pid),
                "style": pdata.get("style", ""),
                "avatar": pdata.get("avatar", "🤖"),
                "description": pdata.get("description", ""),
            }
            for pid, pdata in personas.items()
        ],
        "default": "professor",
    }


@router.post("/switch")
def switch_persona(req: PersonaSwitchRequest):
    """切换用户的 AI 人格。

    人格 ID 存储在用户 profile 中，Orchestrator 每轮对话时读取。
    """
    personas = _load_personas()
    if req.persona_id not in personas:
        raise HTTPException(
            status_code=400,
            detail=f"无效的人格 ID: {req.persona_id}，可选: {list(personas.keys())}",
        )
    # 读取当前 profile 并写入 persona_id
    current_profile = ProfileRepository.get(req.user_id) or {}
    current_profile["persona_id"] = req.persona_id
    ProfileRepository.upsert(req.user_id, current_profile)

    persona = personas[req.persona_id]
    logger.info("[Persona] 用户 %s 切换人格 -> %s", req.user_id, req.persona_id)
    return {
        "status": "ok",
        "user_id": req.user_id,
        "persona_id": req.persona_id,
        "persona_name": persona.get("name", req.persona_id),
        "persona_avatar": persona.get("avatar", "🤖"),
    }


@router.get("/current/{user_id}")
def get_current_persona(user_id: str):
    """获取用户当前的 AI 人格设置。"""
    profile = ProfileRepository.get(user_id) or {}
    persona_id = profile.get("persona_id", "professor")
    personas = _load_personas()
    persona = personas.get(persona_id, personas.get("professor", {}))
    return {
        "user_id": user_id,
        "persona_id": persona_id,
        "persona_name": persona.get("name", persona_id),
        "persona_avatar": persona.get("avatar", "🤖"),
        "persona_description": persona.get("description", ""),
    }
