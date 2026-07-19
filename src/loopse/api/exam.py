"""证书模拟考试 API。"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..agent.challenger import (
    get_exam_session,
    list_exams,
    start_exam_session,
    submit_exam,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/exam", tags=["exam"])


class StartExamRequest(BaseModel):
    user_id: str = Field(default="student-001")
    exam_id: str = Field(..., description="考试 ID：hcia_mock / ccna_mock / computer_network_exam")
    question_count: int = Field(default=20, ge=5, le=50, description="抽题数量")
    weak_kp_ids: list[str] = Field(default_factory=list, description="薄弱知识点 ID 列表，用于加权抽题")


class SubmitExamRequest(BaseModel):
    answers: dict[str, str] = Field(..., description="{question_id: answer} 映射，如 {hcia_001: 'C'}")


@router.get("/list")
def get_exam_list():
    """获取可用考试列表。"""
    return {"exams": list_exams()}


@router.post("/start")
def start_exam(req: StartExamRequest):
    """开始模拟考试，返回题目列表（不含答案）。"""
    result = start_exam_session(
        user_id=req.user_id,
        exam_id=req.exam_id,
        question_count=req.question_count,
        weak_kp_ids=req.weak_kp_ids or None,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/submit/{session_id}")
def submit(session_id: str, req: SubmitExamRequest):
    """提交答案，返回成绩报告和错题诊断。"""
    result = submit_exam(session_id, req.answers)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/session/{session_id}")
def get_session(session_id: str):
    """获取考试会话状态（答题进度）。"""
    state = get_exam_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    # 返回状态但不暴露题目答案
    return {
        "session_id": session_id,
        "exam_id": state.get("exam_id"),
        "exam_name": state.get("exam_name"),
        "status": state.get("status"),
        "question_count": len(state.get("questions", [])),
        "answered_count": len(state.get("answers", {})),
        "score": state.get("score"),
    }


@router.get("/history/{user_id}")
def get_history(user_id: str):
    """获取用户历史考试记录（内存中的已完成会话）。"""
    from ..agent.challenger import challenger_agent
    completed = []
    for sid, state in challenger_agent._sessions.items():
        if state.get("user_id") == user_id and state.get("status") == "completed" and "score" in state:
            completed.append({
                "session_id": sid,
                "exam_id": state.get("exam_id"),
                "exam_name": state.get("exam_name"),
                "score": state.get("score"),
                "question_count": len(state.get("questions", [])),
            })
    return {"user_id": user_id, "history": completed}
