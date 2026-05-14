from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from src.loopse.core.llm_client import llm_client
from src.loopse.agents.retriever import retriever_agent

router = APIRouter(prefix="/api/v1/chat")

class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    context = retriever_agent.search_knowledge(request.message, n_results=3)
    context_text = "\n".join([r["content"] for r in context]) if context else ""
    system_prompt = f"你是计算机网络学习教练，基于以下知识库回答：\n{context_text}"

    async def sse_generator():
        try:
            async for token in llm_client.async_stream_chat(
                user_message=request.message,
                system_prompt=system_prompt
            ):
                yield f"data: {json.dumps({'event': 'token', 'data': token, 'agent_name': 'Orchestrator'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'data': str(e)})}\n\n"
        finally:
            yield f"data: {json.dumps({'event': 'done'})}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
