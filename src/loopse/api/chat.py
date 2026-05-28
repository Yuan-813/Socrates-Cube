"""Chat streaming routes."""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from ..agents.orchestrator import OrchestratorAgent
from ..db.repositories import SessionRepository, UserRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
_orchestrator = OrchestratorAgent()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(default="student-001")
    session_id: str | None = None


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    UserRepository.get_or_create(req.user_id)
    session_id = req.session_id or str(uuid.uuid4())
    SessionRepository.get_or_create(session_id=session_id, user_id=req.user_id)
    logger.info("chat request session=%s user=%s", session_id, req.user_id)

    async def event_generator():
        async for chunk in _orchestrator.async_stream_reply(session_id, req.user_id, req.message):
            yield chunk

    return EventSourceResponse(event_generator(), media_type="text/event-stream")
