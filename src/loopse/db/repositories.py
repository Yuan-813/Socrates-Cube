"""
数据访问封装层 —— Agent 层通过此模块读写数据库，禁止直接操作 ORM
"""
import json
import uuid
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy.orm import Session

from src.loopse.db.connection import SessionLocal
from src.loopse.db.models import User, StudentProfile, ChatSession, AgentLog


@contextmanager
def get_db_session():
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class UserRepository:
    @staticmethod
    def get_or_create(username: str) -> dict:
        with get_db_session() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                user = User(id=str(uuid.uuid4()), username=username)
                db.add(user)
                db.flush()
                db.refresh(user)
            return {"id": user.id, "username": user.username}


class ProfileRepository:
    @staticmethod
    def get(user_id: str) -> dict | None:
        with get_db_session() as db:
            record = db.query(StudentProfile).filter(
                StudentProfile.user_id == user_id
            ).first()
            if not record:
                return None
            return json.loads(record.profile_json)

    @staticmethod
    def upsert(user_id: str, profile: dict):
        with get_db_session() as db:
            record = db.query(StudentProfile).filter(
                StudentProfile.user_id == user_id
            ).first()
            if record:
                record.profile_json = json.dumps(profile, ensure_ascii=False)
                record.update_time = datetime.now()
            else:
                record = StudentProfile(
                    user_id=user_id,
                    profile_json=json.dumps(profile, ensure_ascii=False),
                )
                db.add(record)


class SessionRepository:
    @staticmethod
    def get_or_create(session_id: str, user_id: str) -> dict:
        with get_db_session() as db:
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()
            if not session:
                session = ChatSession(
                    session_id=session_id,
                    user_id=user_id,
                    messages="[]",
                )
                db.add(session)
                db.flush()
                db.refresh(session)
            return {"session_id": session.session_id, "user_id": session.user_id}

    @staticmethod
    def append_message(session_id: str, role: str, content: str):
        with get_db_session() as db:
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()
            if session:
                msgs = json.loads(session.messages or "[]")
                msgs.append({
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                })
                session.messages = json.dumps(msgs, ensure_ascii=False)

    @staticmethod
    def get_turn_count(session_id: str) -> int:
        with get_db_session() as db:
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()
            if not session:
                return 0
            msgs = json.loads(session.messages or "[]")
            return len([m for m in msgs if m.get("role") == "user"])


class AgentLogRepository:
    @staticmethod
    def write(
        session_id: str,
        agent_name: str,
        action: str,
        input_state: dict,
        output_state: dict,
        duration_ms: int = 0,
    ):
        with get_db_session() as db:
            log = AgentLog(
                log_id=str(uuid.uuid4()),
                session_id=session_id,
                agent_name=agent_name,
                action=action,
                state=json.dumps(
                    {"input": input_state, "output": output_state},
                    ensure_ascii=False,
                ),
                timestamp=datetime.now(),
                result=json.dumps(output_state, ensure_ascii=False),
            )
            db.add(log)

    @staticmethod
    def get_session_logs(session_id: str) -> list:
        with get_db_session() as db:
            logs = (
                db.query(AgentLog)
                .filter(AgentLog.session_id == session_id)
                .order_by(AgentLog.timestamp)
                .all()
            )
            return [
                {
                    "log_id": lg.log_id,
                    "agent_name": lg.agent_name,
                    "action": lg.action,
                    "timestamp": lg.timestamp.isoformat(),
                }
                for lg in logs
            ]
