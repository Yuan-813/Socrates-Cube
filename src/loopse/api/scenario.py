"""情景对话 API 接口。"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..agent.scenario_agent import scenario_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/scenario", tags=["scenario"])


class StartScenarioRequest(BaseModel):
    user_id: str = Field(default="student-001")
    scenario_id: str = Field(..., description="场景ID: enterprise_troubleshoot/team_networking/campus_lab")
    user_role: Optional[str] = Field(default=None, description="用户扮演的角色ID（空则使用默认角色）")


class DialogueRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


@router.get("/list")
def list_scenarios():
    """获取所有可用情景列表。"""
    return {"scenarios": scenario_agent.list_scenarios()}


@router.post("/start")
def start_scenario(req: StartScenarioRequest):
    """开始情景对话会话。"""
    result = scenario_agent.start_session(req.user_id, req.scenario_id, req.user_role)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/dialogue/{session_id}")
def advance_dialogue(session_id: str, req: DialogueRequest):
    """用户发言，获取AI角色回应。"""
    responses = scenario_agent.advance_dialogue(session_id, req.message)
    if responses and responses[0].get("error"):
        raise HTTPException(status_code=404, detail=responses[0]["content"])
    return {"session_id": session_id, "responses": responses}


@router.get("/session/{session_id}")
def get_session(session_id: str):
    """获取情景会话状态。"""
    state = scenario_agent.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    return {
        "session_id": session_id,
        "scenario_id": state["scenario_id"],
        "scenario_name": state["scenario_name"],
        "status": state["status"],
        "turn": state["turn"],
        "history_count": len(state["history"]),
    }


@router.post("/end/{session_id}")
def end_scenario(session_id: str):
    """结束情景对话，生成学习总结。"""
    result = scenario_agent.end_session(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
