"""数据访问封装层，供 Agent 层调用，禁止 Agent 直接操作 db"""

from sqlalchemy import select
from src.loopse.db.connection import async_session
from src.loopse.db.models import User, StudentProfile, ChatSession, AgentLog
import json
import uuid
from datetime import datetime


class UserRepository:
    @staticmethod
    async def get_or_create(username: str) -> dict:
        async with async_session() as db:
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            if not user:
                user = User(id=str(uuid.uuid4()), username=username)
                db.add(user)
                await db.commit()
                await db.refresh(user)
            return {"id": user.id, "username": user.username}


class ProfileRepository:
    @staticmethod
    async def get(user_id: str) -> dict | None:
        async with async_session() as db:
            result = await db.execute(
                select(StudentProfile).where(StudentProfile.user_id == user_id)
            )
            record = result.scalar_one_or_none()
            return json.loads(record.profile_json) if record else None

    @staticmethod
    async def upsert(user_id: str, profile: dict):
        async with async_session() as db:
            result = await db.execute(
                select(StudentProfile).where(StudentProfile.user_id == user_id)
            )
            record = result.scalar_one_or_none()
            if record:
                record.profile_json = json.dumps(profile, ensure_ascii=False)
                record.update_time = datetime.now()
            else:
                record = StudentProfile(
                    user_id=user_id,
                    profile_json=json.dumps(profile, ensure_ascii=False)
                )
                db.add(record)
            await db.commit()


class SessionRepository:
    @staticmethod
    async def get_or_create(session_id: str, user_id: str) -> dict:
        async with async_session() as db:
            result = await db.execute(
                select(ChatSession).where(ChatSession.session_id == session_id)
            )
            session = result.scalar_one_or_none()
            if not session:
                session = ChatSession(
                    session_id=session_id,
                    user_id=user_id,
                    messages="[]"
                )
                db.add(session)
                await db.commit()
                await db.refresh(session)
            return {"session_id": session.session_id, "user_id": session.user_id}

    @staticmethod
    async def append_message(session_id: str, role: str, content: str):
        async with async_session() as db:
            result = await db.execute(
                select(ChatSession).where(ChatSession.session_id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                msgs = json.loads(session.messages or "[]")
                msgs.append({
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                })
                session.messages = json.dumps(msgs, ensure_ascii=False)
                await db.commit()


class AgentLogRepository:
    @staticmethod
    async def write(session_id: str, agent_name: str, action: str,
                    input_state: dict, output_state: dict, duration_ms: int = 0):
        async with async_session() as db:
            log = AgentLog(
                log_id=str(uuid.uuid4()),
                session_id=session_id,
                agent_name=agent_name,
                action=action,
                state=json.dumps({
                    "input": input_state,
                    "output": output_state
                }, ensure_ascii=False),
                timestamp=datetime.now(),
                result=json.dumps(output_state, ensure_ascii=False)
            )
            db.add(log)
            await db.commit()

    @staticmethod
    async def get_session_logs(session_id: str) -> list:
        async with async_session() as db:
            result = await db.execute(
                select(AgentLog)
                .where(AgentLog.session_id == session_id)
                .order_by(AgentLog.timestamp)
            )
            logs = result.scalars().all()
            return [
                {
                    "log_id": l.log_id,
                    "agent_name": l.agent_name,
                    "action": l.action,
                    "timestamp": l.timestamp.isoformat() if l.timestamp else "",
                    "result": l.result,
                }
                for l in logs
            ]
