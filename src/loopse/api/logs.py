"""Agent log routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..db.repositories import AgentLogRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


@router.get("/session/{session_id}")
def get_session_logs(session_id: str):
    try:
        return {"session_id": session_id, "logs": AgentLogRepository.get_session_logs(session_id)}
    except Exception as exc:
        logger.error("query logs failed session=%s: %s", session_id, exc)
        raise HTTPException(status_code=500, detail="log query failed") from exc
