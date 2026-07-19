"""Chat streaming routes.

SSE 稳定性：包含 heartbeat 机制，防止代理超时断连。
"""
from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from ..agent.orchestrator import OrchestratorAgent
from ..db.repositories import SessionRepository, UserRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
_orchestrator = OrchestratorAgent()

# SSE heartbeat 间隔（秒），防止代理超时断连
_HEARTBEAT_INTERVAL = 15


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(default="student-001")
    session_id: str | None = None
    agent_persona: str = Field(default="professor", description="智能体人格: professor/peer/expert")


@router.get("/test")
async def chat_test():
    """Phase 0 验收：后端联通测试接口"""
    return {"message": "后端联通成功"}


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    # 获取或创建用户，使用返回的真实 DB id（而非 username）
    # 避免 MySQL 外键约束失败（users.id vs username 不一致时就会报 1452）
    # 数据库不可用时降级：直接使用请求中的 user_id，让流程继续
    try:
        user_info = UserRepository.get_or_create(req.user_id)
        actual_user_id = user_info["id"]
    except Exception as db_exc:
        logger.warning("[Chat] DB get_or_create failed (%s), using req.user_id as fallback", db_exc)
        actual_user_id = req.user_id

    session_id = req.session_id or str(uuid.uuid4())
    try:
        SessionRepository.get_or_create(session_id=session_id, user_id=actual_user_id)
    except Exception as db_exc:
        logger.warning("[Chat] SessionRepository.get_or_create failed (%s), continuing without DB session", db_exc)
    logger.info("chat request session=%s user=%s (db_id=%s)", session_id, req.user_id, actual_user_id)

    async def event_generator():
        """SSE 事件生成器，包含 heartbeat 保活机制。"""
        queue: asyncio.Queue = asyncio.Queue()
        done = False

        async def _produce():
            nonlocal done
            try:
                async for chunk in _orchestrator.async_stream_reply(session_id, actual_user_id, req.message, req.agent_persona):
                    await queue.put(chunk)
            except Exception as exc:
                logger.error("[Chat SSE] 生成器异常: %s", exc, exc_info=True)
                err_frame = (
                    'data: {"event": "error", "agent_name": "System",'
                    f' "data": {{"error": "{exc}"}}}}\n\n'
                )
                await queue.put(err_frame)
            finally:
                done = True
                await queue.put(None)  # 哨兵值

        task = asyncio.create_task(_produce())

        try:
            while not done:
                try:
                    chunk = await asyncio.wait_for(queue.get(), timeout=_HEARTBEAT_INTERVAL)
                except asyncio.TimeoutError:
                    # heartbeat：防止代理超时断连
                    yield ": heartbeat\n\n"
                    continue
                if chunk is None:
                    break
                yield chunk
        finally:
            if not task.done():
                task.cancel()

    # 注意：event_generator() 已产出完整的 SSE 帧（"data: ...\n\n" 与
    # ": heartbeat\n\n"），因此必须使用 StreamingResponse 原样透传。若改用
    # EventSourceResponse 会对这些字符串二次包装成 "data: data: ..."，导致
    # 前端 JSON.parse 失败、所有事件被静默丢弃（表现为 AI 无回复）。
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲，保证流式实时到达
        },
    )
