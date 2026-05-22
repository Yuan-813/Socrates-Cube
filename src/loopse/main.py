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
from src.loopse.api.resources import router as resources_router
from src.loopse.api.path import router as path_router
from src.loopse.agent.orchestrator import orchestrator

@asynccontextmanager
async def lifespan(application: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="EduMultiAgent",
    version="0.2.0",
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
app.include_router(resources_router)
app.include_router(path_router)


class ChatStreamRequest(BaseModel):
    session_id: str
    user_id: str
    message: str
    history: list[dict] | None = None


@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "ok", "version": "0.2.0"}


@app.get("/api/v1/chat/test", tags=["对话"])
async def chat_test():
    return {"message": "后端联通成功"}


@app.post("/api/v1/chat/stream", tags=["对话"])
async def chat_stream(payload: ChatStreamRequest):
    async def sse_generator():
        turn_count = 0  # Phase 3从DB读取历史轮数
        async for event_str in orchestrator.process_message(
            session_id=payload.session_id,
            user_id=payload.user_id,
            user_message=payload.message,
            turn_count=turn_count,
        ):
            yield {"data": event_str}

    return EventSourceResponse(sse_generator())
