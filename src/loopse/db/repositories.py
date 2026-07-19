"""Repository layer used by API and agents.

事务保护：get_db_session 包含 commit/rollback/finally close
日志记录：异常时记录完整错误信息
异步写入：AgentLogRepository 支持后台线程写入，不阻塞主流程
"""
from __future__ import annotations

import json
import logging
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

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

logger = logging.getLogger(__name__)


@contextmanager
def get_db_session() -> Iterator[Session]:
    """获取 DB 会话，包含事务提交 / 回滚 / 关闭全流程。

    异常处理：捕获并记录日志后重新抛出，确保上层可感知。
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("[DB] 事务回滚: %s", exc, exc_info=True)
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
            # 优先按 id（=username）查找，兴容旧 UUID 写入的历史数据
            user = db.query(User).filter(
                (User.id == username) | (User.username == username)
            ).first()
            if not user:
                # 使用 username 作为 id，确保下游的 session/profile 外键不会违约
                user = User(id=username, username=username)
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
        """写入 Agent 日志。

        默认同步写入。如果调用方在异步上下文中且不关心写入结果，
        可调用 write_async 方法避免阻塞主流程。
        """
        payload = {"input": input_state, "output": output_state, "duration_ms": duration_ms}
        try:
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
        except Exception as exc:
            logger.warning("[DB] AgentLog 写入失败 (非致命): %s", exc)

    @staticmethod
    def write_async(
        session_id: str,
        agent_name: str,
        action: str,
        input_state: dict | str,
        output_state: dict | str,
        duration_ms: int = 0,
    ) -> None:
        """异步写入 Agent 日志，不阻塞主流程。

        使用后台线程执行 DB 写入，异常时仅记录日志不抛出。
        """
        def _write():
            try:
                AgentLogRepository.write(
                    session_id, agent_name, action, input_state, output_state, duration_ms
                )
            except Exception as exc:
                logger.warning("[DB] async AgentLog 写入失败: %s", exc)

        thread = threading.Thread(target=_write, daemon=True)
        thread.start()

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
        """返回最近生成的有效资源（内容长度 >= 100 字符，排除占位符数据）。"""
        with get_db_session() as db:
            rows = (
                db.query(LearningResource)
                .filter(sa_func.length(LearningResource.content) >= 100)
                .order_by(LearningResource.create_time.desc())
                .limit(limit)
                .all()
            )
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
