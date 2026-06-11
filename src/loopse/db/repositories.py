"""Repository layer used by API and agents."""
from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

from sqlalchemy.orm import Session

from src.loopse.db.connection import SessionLocal
from src.loopse.db.models import (
    AgentLog,
    ChatSession,
    LearningPath,
    LearningPathNode,
    LearningResource,
    StudentProfile,
    User,
)


@contextmanager
def get_db_session() -> Iterator[Session]:
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _loads(text: str | None, default: Any) -> Any:
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default


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
            record = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
            return _loads(record.profile_json, {}) if record else None

    @staticmethod
    def upsert(user_id: str, profile: dict | str) -> None:
        profile_json = profile if isinstance(profile, str) else json.dumps(profile, ensure_ascii=False)
        with get_db_session() as db:
            record = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
            if record:
                record.profile_json = profile_json
                record.update_time = datetime.now()
            else:
                db.add(StudentProfile(user_id=user_id, profile_json=profile_json))


class SessionRepository:
    @staticmethod
    def get_or_create(session_id: str | None = None, user_id: str | None = None) -> dict:
        sid = session_id or str(uuid.uuid4())
        with get_db_session() as db:
            session = db.query(ChatSession).filter(ChatSession.session_id == sid).first()
            if not session:
                session = ChatSession(session_id=sid, user_id=user_id, messages="[]")
                db.add(session)
                db.flush()
                db.refresh(session)
            return {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "messages": _loads(session.messages, []),
            }

    @staticmethod
    def append_message(session_id: str, role: str | dict, content: str | None = None) -> None:
        if isinstance(role, dict):
            message = role
        else:
            message = {"role": role, "content": content or "", "timestamp": datetime.now().isoformat()}

        with get_db_session() as db:
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if not session:
                session = ChatSession(session_id=session_id, messages="[]")
                db.add(session)
                db.flush()
            msgs = _loads(session.messages, [])
            msgs.append(message)
            session.messages = json.dumps(msgs[-80:], ensure_ascii=False)
            session.update_time = datetime.now()

    @staticmethod
    def get_turn_count(session_id: str) -> int:
        with get_db_session() as db:
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            msgs = _loads(session.messages if session else "[]", [])
            return len([m for m in msgs if m.get("role") == "user"])


class AgentLogRepository:
    @staticmethod
    def write(
        session_id: str,
        agent_name: str,
        action: str,
        input_state: dict | str,
        output_state: dict | str,
        duration_ms: int = 0,
    ) -> None:
        payload = {"input": input_state, "output": output_state, "duration_ms": duration_ms}
        with get_db_session() as db:
            db.add(
                AgentLog(
                    log_id=str(uuid.uuid4()),
                    session_id=session_id,
                    agent_name=agent_name,
                    action=action,
                    state=json.dumps(payload, ensure_ascii=False, default=str),
                    result=json.dumps(output_state, ensure_ascii=False, default=str),
                )
            )

    @staticmethod
    def get_session_logs(session_id: str) -> list[dict]:
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
                    "state": _loads(lg.state, {}),
                    "result": _loads(lg.result, {}),
                    "timestamp": lg.timestamp.isoformat(),
                }
                for lg in logs
            ]


class ResourceRepository:
    @staticmethod
    def save(resource: dict) -> None:
        with get_db_session() as db:
            db.merge(
                LearningResource(
                    resource_id=resource["resource_id"],
                    knowledge_node_id=resource.get("knowledge_node_id"),
                    knowledge_point=resource["knowledge_point"],
                    resource_type=resource["resource_type"],
                    difficulty=resource.get("metadata", {}).get("difficulty", 3),
                    title=resource["title"],
                    content=resource["content"],
                    metadata_json=json.dumps(resource.get("metadata", {}), ensure_ascii=False),
                    quality_score=resource.get("quality_score", 0.75),
                )
            )

    @staticmethod
    def list_recent(limit: int = 20) -> list[dict]:
        with get_db_session() as db:
            rows = db.query(LearningResource).order_by(LearningResource.create_time.desc()).limit(limit).all()
            return [
                {
                    "resource_id": r.resource_id,
                    "resource_type": r.resource_type,
                    "knowledge_point": r.knowledge_point,
                    "title": r.title,
                    "content": r.content,
                    "metadata": _loads(r.metadata_json, {}),
                    "quality_score": r.quality_score,
                    "created_at": r.create_time.isoformat(),
                }
                for r in rows
            ]


class LearningPathRepository:
    @staticmethod
    def save(path: dict) -> None:
        with get_db_session() as db:
            db.merge(
                LearningPath(
                    path_id=path["path_id"],
                    user_id=path["user_id"],
                    title=path["title"],
                    description=path.get("description", ""),
                    total_estimated_time=path.get("total_estimated_time", 0),
                    plan_json=json.dumps(path, ensure_ascii=False),
                )
            )
            for index, node in enumerate(path.get("nodes", []), start=1):
                db.merge(
                    LearningPathNode(
                        id=f"{path['path_id']}:{node['node_id']}",
                        path_id=path["path_id"],
                        node_id=node["node_id"],
                        sequence=index,
                        status=node.get("status", "pending"),
                        current_mastery=node.get("current_mastery", 0.0),
                        recommendation_reason=node.get("recommendation_reason", ""),
                    )
                )
