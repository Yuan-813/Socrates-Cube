"""Challenger API — 误解对抗检验接口。"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..agent.challenger import challenger_agent
from ..agent.profiler import ProfilerAgent

router = APIRouter(prefix="/api/v1/challenger", tags=["challenger"])
_profiler = ProfilerAgent()


class ChallengerStartRequest(BaseModel):
    session_id: str
    user_id: str = "default"
    diagnosis: Optional[dict[str, Any]] = None


class ChallengerEvaluateRequest(BaseModel):
    session_id: str
    user_answer: str = Field(..., min_length=1)


@router.post("/start")
def start_challenge(req: ChallengerStartRequest) -> dict[str, Any]:
    diagnosis = req.diagnosis or {
        "is_correct": False,
        "surface_error": "TCP 三次握手流程理解不完整",
        "pattern": "流程遗漏型",
        "intervention_suggestion": "用失效连接请求反例说明第三次 ACK 的必要性",
    }
    profile = _profiler.get_profile(req.user_id)
    result = challenger_agent.start_session(req.session_id, diagnosis, profile)
    return {"status": "ok", "challenge": result}


@router.post("/evaluate")
def evaluate_answer(req: ChallengerEvaluateRequest) -> dict[str, Any]:
    result = challenger_agent.evaluate_answer(req.session_id, req.user_answer)
    if result.get("status") == "inactive":
        raise HTTPException(status_code=404, detail=result.get("message", "无进行中的检验"))
    return {"status": "ok", "result": result}


@router.get("/session/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    state = challenger_agent.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"status": "ok", "session": state}
