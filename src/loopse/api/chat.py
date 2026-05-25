"""
/api/v1/chat 路由：处理 SSE 流式对话
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from ...agents.orchestrator import OrchestratorAgent
from ...db.repositories import SessionRepository, UserRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

_orchestrator = OrchestratorAgent()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="学生消息")
    user_id: str = Field(default="student-001", description="用户ID")
    session_id: str | None = Field(default=None, description="会话ID（空时自动创建）")


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    """
    SSE 流式对话接口。
    返回 text/event-stream，每条消息格式：data: {...JSON...}\\n\\n
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    # 确保用户存在
    try:
        UserRepository.get_or_create(req.user_id)
    except Exception as e:
        logger.warning("用户创建失败（非致命）: %s", e)

    # 获取或创建会话
    session_id = req.session_id
    if not session_id:
        try:
            sess = SessionRepository.get_or_create(user_id=req.user_id)
            session_id = sess["session_id"]
        except Exception:
            import uuid
            session_id = str(uuid.uuid4())

    logger.info("收到对话请求 session=%s user=%s", session_id, req.user_id)

    async def event_generator():
        async for chunk in _orchestrator.async_stream_reply(
            session_id=session_id,
            user_id=req.user_id,
            user_message=req.message,
        ):
            # chunk 已经是 "data: {...}\n\n" 格式，直接 yield
            yield chunk

    return EventSourceResponse(event_generator(), media_type="text/event-stream")
