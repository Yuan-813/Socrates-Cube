"""
/api/v1/logs 路由：代理运行日志查询
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ...db.repositories import AgentLogRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


@router.get("/session/{session_id}")
def get_session_logs(session_id: str):
    """获取指定会话的所有代理运行日志"""
    try:
        logs = AgentLogRepository.get_session_logs(session_id)
        return {"session_id": session_id, "logs": logs}
    except Exception as e:
        logger.error("查询日志失败 session=%s: %s", session_id, e)
        raise HTTPException(status_code=500, detail="日志查询失败")
