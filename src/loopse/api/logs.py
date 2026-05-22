from fastapi import APIRouter
from src.loopse.db.repositories import AgentLogRepository

router = APIRouter(prefix="/api/v1/logs", tags=["日志"])


@router.get("/session/{session_id}")
async def get_session_logs(session_id: str):
    logs = await AgentLogRepository.get_session_logs(session_id)
    return {"session_id": session_id, "logs": logs, "total": len(logs)}
