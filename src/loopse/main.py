from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

from src.loopse.db.connection import init_db
from src.loopse.db.repositories import AgentLogRepository
from src.loopse.api.profile import router as profile_router
from src.loopse.api.logs import router as logs_router

@asynccontextmanager
async def lifespan(application: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="EduMultiAgent",
    version="0.1.0",
    description="Socrates-Cube 多智能体自适应学习系统",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_router)
app.include_router(logs_router)


class ChatStreamRequest(BaseModel):
    session_id: str
    user_id: str
    message: str
    history: list[dict] | None = None


@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/v1/chat/test", tags=["对话"])
async def chat_test():
    return {"message": "后端联通成功"}


@app.post("/api/v1/chat/stream", tags=["对话"])
async def chat_stream(payload: ChatStreamRequest):
    import time
    start_time = time.time()

    async def event_generator():
        start_event = {
            "event": "agent_start",
            "agent_name": "Orchestrator",
            "data": f"开始处理问题：{payload.message}",
        }
        yield {
            "data": json.dumps(start_event, ensure_ascii=False)
        }

        reply = (
            f"收到你的问题：{payload.message}。"
            "这是后端 real 模式返回的最小联调流式结果，"
            "前端已经可以据此验证 SSE 主链路、模式切换与联动展示。"
        )

        for char in reply:
            token_event = {
                "event": "token",
                "agent_name": "Orchestrator",
                "data": char,
            }
            yield {
                "data": json.dumps(token_event, ensure_ascii=False)
            }
            await asyncio.sleep(0.02)

        # 写入 AgentLog
        duration_ms = int((time.time() - start_time) * 1000)
        await AgentLogRepository.write(
            session_id=payload.session_id,
            agent_name="Orchestrator",
            action="chat_stream",
            input_state={"user_message": payload.message},
            output_state={"reply_length": len(reply)},
            duration_ms=duration_ms,
        )

        agent_end_event = {
            "event": "agent_end",
            "agent_name": "Orchestrator",
            "data": {"status": "done", "duration_ms": duration_ms},
        }
        yield {
            "data": json.dumps(agent_end_event, ensure_ascii=False)
        }

        done_event = {
            "event": "done",
            "agent_name": "Orchestrator",
            "data": "done",
        }
        yield {
            "data": json.dumps(done_event, ensure_ascii=False)
        }

    return EventSourceResponse(event_generator())
